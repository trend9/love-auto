import os
import json
import random
import subprocess
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths / Settings
# =========================
MODEL_PATH = "./models/model.gguf"

QUESTIONS_PATH = "data/questions.json"
USED_QUESTIONS_PATH = "data/used_questions.json"

POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
SITEMAP_PATH = "sitemap.xml"

SITE_URL = "https://trend9.github.io/love-auto"
AUTHOR_NAME = "ゆい姉さん"
GOOGLE_VERIFICATION = "2Xi8IPSGt7YW2_kOHqAzAfaxtgtYvNqiPSB_x8lhto4"

MAX_CONTEXT = 3072

# =========================
# Directories
# =========================
os.makedirs("data", exist_ok=True)
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs("models", exist_ok=True)

# =========================
# LLM Init
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    n_threads=os.cpu_count() or 4,
    n_gpu_layers=0,
    verbose=False
)

# =========================
# Utils
# =========================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else default
    except Exception:
        return default

def save_json(path, data):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_text(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def esc(t):
    return (
        t.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )

# =========================
# Article Generator（下書き）
# =========================
def generate_article_draft(question):
    prompt = f"""
あなたは経験豊富な恋愛カウンセラーです。

【最重要】
- 表面的な一般論・教科書的説明は禁止
- 感情・心理の動きを具体的に言語化する
- 1セクション最低2段落以上
- 全体で1500文字以上
- HTMLタグ以外は出力しない

【構成（厳守）】
<h2>共感と状況整理</h2>
<h2>心理的な背景</h2>
<h2>今日からできる行動</h2>
<h2>やってはいけないNG行動</h2>
<h2>よくある勘違い</h2>
<h2>まとめ</h2>

【相談内容】
{question}
"""
    r = llm(prompt, max_tokens=1900)
    return r["choices"][0]["text"].strip()

# =========================
# Article Generator（清書）
# =========================
def polish_article(draft):
    prompt = f"""
以下の記事を、人間が本気で書いた恋愛相談記事として清書してください。

【清書ルール】
- 冗長な繰り返しは整理
- 感情の流れを自然に
- 上から目線・断定口調は禁止
- 読者が「自分のことだ」と感じる温度感を重視

【厳守】
- 構成・見出し・HTMLタグは絶対に変えない
- 内容の水増し・削除は禁止（表現の改善のみ）

【記事】
{draft}
"""
    r = llm(prompt, max_tokens=1800)
    return r["choices"][0]["text"].strip()

# =========================
# Summary
# =========================
def generate_summary(content):
    prompt = f"""
以下の記事を120〜160文字で要約してください。
抽象語は禁止。具体的に。改行なし。

本文：
{content[:1600]}
"""
    r = llm(prompt, max_tokens=300)
    return r["choices"][0]["text"].strip().replace("\n", "")

# =========================
# 内部リンク
# =========================
def related_links(questions, current_id, limit=3):
    others = [q for q in questions if q.get("id") != current_id]
    random.shuffle(others)
    picks = others[:limit]

    if not picks:
        return ""

    html = "<h2>関連記事</h2><ul>"
    for q in picks:
        html += f'<li><a href="/{q["url"]}">{esc(q["title"])}</a></li>'
    html += "</ul>"
    return html

# =========================
# Schema / Canonical / Sitemap
# =========================
def author_schema():
    return f"""
<script type="application/ld+json">
{{
 "@context":"https://schema.org",
 "@type":"Person",
 "name":"{AUTHOR_NAME}",
 "jobTitle":"恋愛相談アドバイザー"
}}
</script>
"""

def article_schema(title, summary, slug):
    return f"""
<script type="application/ld+json">
{{
 "@context":"https://schema.org",
 "@type":"Article",
 "headline":"{esc(title)}",
 "description":"{esc(summary)}",
 "author":{{"@type":"Person","name":"{AUTHOR_NAME}"}},
 "mainEntityOfPage":"{SITE_URL}/posts/{slug}.html",
 "datePublished":"{datetime.now().date()}"
}}
</script>
"""

def faq_schema(title, question):
    return f"""
<script type="application/ld+json">
{{
 "@context":"https://schema.org",
 "@type":"FAQPage",
 "mainEntity":[
  {{
   "@type":"Question",
   "name":"{esc(title)}",
   "acceptedAnswer":{{"@type":"Answer","text":"{esc(question)}"}}
  }}
 ]
}}
</script>
"""

def canonical(slug):
    return f'<link rel="canonical" href="{SITE_URL}/posts/{slug}.html">'

def generate_sitemap(questions):
    xml = ""
    for q in questions:
        if "url" in q:
            xml += f"<url><loc>{SITE_URL}/{q['url']}</loc></url>\n"

    save_text(
        SITEMAP_PATH,
        f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml}
</urlset>"""
    )

# =========================
# Main（質問生成失敗＝即失敗）
# =========================
def main():
    result = subprocess.run(
        ["python", "question_generator.py"],
        check=False
    )
    if result.returncode != 0:
        raise RuntimeError("質問生成に失敗したため処理を中断")

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_QUESTIONS_PATH, [])

    used_ids = {u["id"] for u in used if "id" in u}
    unused = [q for q in questions if q["id"] not in used_ids]

    if not unused:
        raise RuntimeError("未使用の質問が存在しない（異常）")

    q = unused[0]

    draft = generate_article_draft(q["question"])
    content = polish_article(draft)
    summary = generate_summary(content)

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    content_with_links = content + related_links(questions, q["id"])

    html = (
        tpl.replace("{{TITLE}}", esc(q["title"]))
           .replace("{{META_DESCRIPTION}}", esc(summary))
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{q['slug']}.html")
           .replace("{{CANONICAL}}", canonical(q["slug"]))
           .replace("{{DATE_JP}}", datetime.now().strftime("%Y年%m月%d日"))
           .replace("{{DATE_ISO}}", datetime.now().isoformat())
           .replace("{{CONTENT}}", content_with_links)
           .replace("{{AUTHOR_SCHEMA}}", author_schema())
           .replace("{{ARTICLE_SCHEMA}}", article_schema(q["title"], summary, q["slug"]))
           .replace("{{FAQ_SCHEMA}}", faq_schema(q["title"], q["question"]))
           .replace(
               "{{GOOGLE_VERIFY}}",
               f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}" />'
           )
    )

    save_text(os.path.join(POST_DIR, f"{q['slug']}.html"), html)

    used.append({"id": q["id"]})
    save_json(USED_QUESTIONS_PATH, used)

    generate_sitemap(questions)
    print("✅ 記事生成 完了")

if __name__ == "__main__":
    main()
