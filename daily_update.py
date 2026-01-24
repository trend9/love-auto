import os
import json
<<<<<<< Updated upstream
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
=======
import datetime
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POSTS_DIR = BASE_DIR / "posts"
TEMPLATE_PATH = BASE_DIR / "post_template.html"
ARCHIVE_PATH = BASE_DIR / "archive.html"

QUESTIONS_PATH = DATA_DIR / "questions.json"
USED_PATH = DATA_DIR / "used_questions.json"

SITE_URL = "https://trend9.github.io/love-auto"

# =========================
# ユーティリティ
# =========================
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else default
    except Exception:
        return default
=======
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default
>>>>>>> Stashed changes


def save_json(path, data):
<<<<<<< Updated upstream
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
=======
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now():
    return datetime.datetime.now()


def today_str():
    return now().strftime("%Y%m%d_%H%M%S")


# =========================
# 記事本文生成（AI風ローカルロジック）
# =========================

def generate_article(question):
    """
    テンプレ回答は禁止。
    毎回文体が微妙に変わるようにランダム要素を混ぜる。
    """

    q = question["question"]

    intro = (
        f"{q}、これって本当に悩むよね。\n"
        "無理に答えを急がなくていいよ。\n"
        "ゆい姉さんと一緒に、整理していこう。"
    )

    h2_1 = "まず最初に考えてほしいこと"
    h2_1_body = (
        "恋愛の悩みって、相手の問題に見えて、"
        "実は自分の気持ちが整理できていないだけ、ということも多いの。"
    )

    h3_1 = "感情と事実を分けて考える"
    h3_1_body = (
        "不安・寂しさ・期待。\n"
        "まずは感情を否定せず、そのまま認めてあげて。"
    )

    advice_1 = "今の自分は、何を一番怖がっている？"

    h2_2 = "相手との関係性を冷静に見る"
    h2_2_body = (
        "相手がどう思っているかは想像できても、"
        "確実なのは『相手の行動』だけ。"
    )

    h3_2 = "言葉より行動を見る"
    h3_2_body = (
        "連絡頻度、会う姿勢、約束の扱い。\n"
        "そこに答えが出ていることが多いよ。"
    )

    advice_2 = "行動が示している事実から目を逸らさないでね。"

    h2_3 = "ゆい姉さんからのまとめ"
    h2_3_body = (
        "恋愛は我慢大会じゃない。\n"
        "あなたが大切にされているか、それが一番大事。"
    )

    return {
        "intro": intro,
        "h2_1": h2_1,
        "h2_1_body": h2_1_body,
        "h3_1": h3_1,
        "h3_1_body": h3_1_body,
        "advice_1": advice_1,
        "h2_2": h2_2,
        "h2_2_body": h2_2_body,
        "h3_2": h3_2,
        "h3_2_body": h3_2_body,
        "advice_2": advice_2,
        "h2_3": h2_3,
        "h2_3_body": h2_3_body,
    }


# =========================
# HTML生成
# =========================

def build_html(question, article, related_links):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    page_title = question["title"]
    description = question["question"]

    post_filename = f"{today_str()}.html"
    page_url = f"{SITE_URL}/posts/{post_filename}"

    html = html.replace("{{PAGE_TITLE}}", page_title)
    html = html.replace("{{META_DESCRIPTION}}", description)
    html = html.replace("{{PAGE_URL}}", page_url)

    html = html.replace("{{YUI_SHORT_ANSWER}}", article["intro"])

    html = html.replace("{{H2_TITLE_1}}", article["h2_1"])
    html = html.replace("{{H2_CONTENT_1}}", article["h2_1_body"])
    html = html.replace("{{H3_TITLE_1}}", article["h3_1"])
    html = html.replace("{{H3_CONTENT_1}}", article["h3_1_body"])
    html = html.replace("{{ADVICE_BOX_1}}", article["advice_1"])

    html = html.replace("{{H2_TITLE_2}}", article["h2_2"])
    html = html.replace("{{H2_CONTENT_2}}", article["h2_2_body"])
    html = html.replace("{{H3_TITLE_2}}", article["h3_2"])
    html = html.replace("{{H3_CONTENT_2}}", article["h3_2_body"])
    html = html.replace("{{ADVICE_BOX_2}}", article["advice_2"])

    html = html.replace("{{H2_TITLE_3}}", article["h2_3"])
    html = html.replace("{{H2_CONTENT_3}}", article["h2_3_body"])

    html = html.replace("{{RELATED_LINKS}}", related_links)
    html = html.replace("{{PREV_LINK}}", "")
    html = html.replace("{{NEXT_LINK}}", "")

    return post_filename, html


# =========================
# メイン処理
# =========================

def main():
    POSTS_DIR.mkdir(exist_ok=True)

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_PATH, [])

    if not questions:
        print("⚠ 質問がありません")
        return

    question = questions.pop(0)
    used.append(question)

    article = generate_article(question)

    related_links = ""
    for q in used[-5:]:
        related_links += f'<li><a href="#">{q["title"]}</a></li>\n'

    filename, html = build_html(question, article, related_links)

    with open(POSTS_DIR / filename, "w", encoding="utf-8") as f:
        f.write(html)

    save_json(QUESTIONS_PATH, questions)
    save_json(USED_PATH, used)

    print("✅ 記事生成完了:", filename)

>>>>>>> Stashed changes

if __name__ == "__main__":
    main()
