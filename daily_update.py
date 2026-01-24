import os
import json
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

MAX_CONTEXT = 2048

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
# Article Generator（薄化防止・失敗不可）
# =========================
def generate_article(question):
    prompt = f"""
あなたは経験豊富な恋愛カウンセラーです。

【最重要】
- 表面的な一般論・教科書的説明は禁止
- 感情・心理の動きを具体的に言語化する
- 1セクション最低2段落以上
- 全体で1500文字以上になるように書く
- HTMLタグ以外は絶対に出力しない

【構成（厳守）】
<h2>共感と状況整理</h2>
<p>相談者の気持ちに深く共感し、状況を具体的に整理する。</p>

<h2>心理的な背景</h2>
<p>相手と相談者、両方の心理を掘り下げる。</p>

<h2>今日からできる行動</h2>
<ul>
<li>感情面</li>
<li>行動面</li>
<li>考え方</li>
</ul>

<h2>やってはいけないNG行動</h2>
<ul>
<li>逆効果になる行動</li>
<li>関係を壊す思考</li>
</ul>

<h2>よくある勘違い</h2>
<p>多くの人が陥る誤解を具体例付きで説明。</p>

<h2>まとめ</h2>
<p>読後に気持ちが少し軽くなる締め。</p>

【相談内容】
{question}
"""
    r = llm(prompt, max_tokens=1900)
    return r["choices"][0]["text"].strip()

def generate_summary(content):
    prompt = f"""
以下の記事を120〜160文字で要約してください。
抽象語は禁止。具体的に。
改行なし、日本語。

本文：
{content[:1600]}
"""
    r = llm(prompt, max_tokens=300)
    return r["choices"][0]["text"].strip().replace("\n", "")

# =========================
# Schema / Canonical / Sitemap
# （※ここ以下は元コード完全維持）
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
# Main（絶対止まらない）
# =========================
def main():
    os.system("python question_generator.py")

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_QUESTIONS_PATH, [])

    if not questions:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        questions = [{
            "id": f"force_{now}",
            "title": "恋愛で不安になったときの心の整え方",
            "slug": f"force-{now}",
            "question": "相手の気持ちが分からず不安になるとき、どう考えればいいでしょうか。",
            "url": f"posts/force-{now}.html"
        }]
        save_json(QUESTIONS_PATH, questions)

    used_ids = {u["id"] for u in used if "id" in u}
    unused = [q for q in questions if q["id"] not in used_ids]
    if not unused:
        used.clear()
        unused = questions[:]

    q = unused[0]

    content = generate_article(q["question"])
    summary = generate_summary(content)

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    html = (
        tpl.replace("{{TITLE}}", esc(q["title"]))
           .replace("{{META_DESCRIPTION}}", esc(summary))
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{q['slug']}.html")
           .replace("{{CANONICAL}}", canonical(q["slug"]))
           .replace("{{DATE_JP}}", datetime.now().strftime("%Y年%m月%d日"))
           .replace("{{DATE_ISO}}", datetime.now().isoformat())
           .replace("{{CONTENT}}", content)
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
