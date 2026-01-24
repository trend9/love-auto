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

SITE_URL = "https://example.com"  # 必ず後で変更
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
# HTML Generators
# =========================
def generate_article(title, question):
    prompt = f"""
あなたは誠実で実用的な恋愛アドバイザーです。
以下の相談に対して、共感→整理→具体的アドバイスの順で丁寧に答えてください。

相談：
{question}
"""
    r = llm(prompt, max_tokens=1800)
    return r["choices"][0]["text"].strip()

def generate_summary(title, content):
    prompt = f"""
以下の記事を120〜160文字で要約してください。

タイトル：
{title}

本文：
{content[:1500]}
"""
    r = llm(prompt, max_tokens=300)
    return r["choices"][0]["text"].strip().replace("\n", "")

# =========================
# Schema
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

# =========================
# Sitemap
# =========================
def generate_sitemap(questions):
    xml = "".join(
        f"<url><loc>{SITE_URL}/{q['url']}</loc></url>"
        for q in questions
        if "url" in q
    )
    save_text(
        SITEMAP_PATH,
        f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml}
</urlset>"""
    )

# =========================
# Main（失敗不可）
# =========================
def main():
    # ① 質問生成（失敗不可設計の question_generator.py）
    os.system("python question_generator.py")

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_QUESTIONS_PATH, [])

    # 最終保険：質問が0件なら強制生成
    if not questions:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        questions = [{
            "id": f"force_{now}",
            "title": "恋愛で不安になったときの心の整え方",
            "slug": f"force-{now}",
            "question": "相手の気持ちが分からず不安になるとき、どう考えればいいでしょうか。",
            "url": f"posts/force-{now}.html"
        }]

    # 未使用質問を選ぶ
    used_ids = {u["id"] for u in used if isinstance(u, dict) and "id" in u}
    unused = [q for q in questions if q.get("id") not in used_ids]
    if not unused:
        used.clear()
        unused = questions[:]

    cur = unused[0]

    # 記事生成
    content = generate_article(cur["title"], cur["question"])
    summary = generate_summary(cur["title"], content)

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    html = (
        tpl.replace("{{TITLE}}", esc(cur["title"]))
           .replace("{{DESCRIPTION}}", esc(summary))
           .replace("{{CONTENT}}", content)
           .replace("{{CANONICAL}}", canonical(cur["slug"]))
           .replace("{{AUTHOR}}", author_schema())
           .replace("{{ARTICLE_SCHEMA}}", article_schema(cur["title"], summary, cur["slug"]))
           .replace("{{FAQ}}", faq_schema(cur["title"], cur["question"]))
           .replace(
               "{{GOOGLE_VERIFY}}",
               f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}" />'
           )
    )

    save_text(os.path.join(POST_DIR, f"{cur['slug']}.html"), html)

    used.append({"id": cur["id"]})
    save_json(USED_QUESTIONS_PATH, used)

    generate_sitemap(questions)

    print("✅ 記事生成 完了")

if __name__ == "__main__":
    main()
