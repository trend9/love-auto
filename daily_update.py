import json
import os
import subprocess
import uuid
from datetime import datetime
from llama_cpp import Llama

# =========================
# 設定
# =========================
MODEL_PATH = "./models/model.gguf"
QUESTIONS_PATH = "data/questions.json"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
SITEMAP_PATH = "sitemap.xml"

SITE_URL = "https://example.com"  # ←必ず自分のドメインに変更
AUTHOR_NAME = "ゆい姉さん"
GOOGLE_VERIFICATION = "2Xi8IPSGt7YW2_kOHqAzAfaxtgtYvNqiPSB_x8lhto4"

# =========================
# LLM
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=os.cpu_count() or 4,
    n_gpu_layers=0,
    verbose=False
)

# =========================
# Utils
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def esc(t):
    return (
        t.replace("&","&amp;")
         .replace("<","&lt;")
         .replace(">","&gt;")
         .replace('"',"&quot;")
    )

# =========================
# Normalize（★ここだけ修正）
# =========================
def normalize(q, index):
    # id が無い・空・壊れている場合は自動生成
    if "id" not in q or not q["id"]:
        q["id"] = f"legacy_{index}_{uuid.uuid4().hex[:8]}"

    # slug が無ければ id を使う
    if not q.get("slug"):
        q["slug"] = q["id"]

    q["url"] = f"posts/{q['slug']}.html"
    return q

# =========================
# AI short summary
# =========================
def generate_summary(title, content):
    prompt = f"""
以下の記事内容を、検索結果やAI回答で使える
120〜160文字の要約にしてください。
説明的・中立・断定しすぎない表現で。

タイトル：
{title}

本文：
{content[:1500]}
"""
    r = llm(prompt, max_tokens=300)
    return r["choices"][0]["text"].strip().replace("\n", "")

# =========================
# Structured Data
# =========================
def author_schema():
    return f"""
<script type="application/ld+json">
{{
 "@context":"https://schema.org",
 "@type":"Person",
 "name":"{AUTHOR_NAME}",
 "jobTitle":"恋愛相談アドバイザー",
 "description":"実体験と相談対応をもとに恋愛の悩みに寄り添う専門家"
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
 "publisher":{{"@type":"Organization","name":"{AUTHOR_NAME}"}},
 "mainEntityOfPage":"{SITE_URL}/posts/{slug}.html",
 "datePublished":"{datetime.now().date()}"
}}
</script>
"""

def faq_schema_multi(title, question):
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
  }},
  {{
   "@type":"Question",
   "name":"どう向き合えばいいですか？",
   "acceptedAnswer":{{"@type":"Answer","text":"自分の気持ちを整理しつつ、相手の立場や状況を尊重する姿勢が大切です。"}}
  }},
  {{
   "@type":"Question",
   "name":"不安になったときの対処法は？",
   "acceptedAnswer":{{"@type":"Answer","text":"一人で抱え込まず、信頼できる人や専門家に相談することで気持ちが軽くなることがあります。"}}
  }}
 ]
}}
</script>
"""

def canonical(slug):
    return f'<link rel="canonical" href="{SITE_URL}/posts/{slug}.html">'

# =========================
# Internal links
# =========================
def similarity(a, b):
    return len(set(a)&set(b)) / max(len(set(a)|set(b)),1)

def internal_links(current, questions, limit=5):
    scored=[]
    for q in questions:
        if q["slug"]==current["slug"]:
            continue
        s=similarity(current["title"],q["title"])
        if s>0:
            scored.append((s,q))
    scored.sort(reverse=True)
    return "".join(
        f'<li><a href="../{q["url"]}">{esc(q["title"])}</a></li>\n'
        for _,q in scored[:limit]
    )

# =========================
# Article generation
# =========================
def generate_article(title, question):
    prompt=f"恋愛相談に対して誠実で実用的なアドバイス記事を書いてください。\n{question}"
    r=llm(prompt,max_tokens=1800)
    return r["choices"][0]["text"].strip()

# =========================
# Sitemap
# =========================
def generate_sitemap(questions):
    xml="".join(
        f"<url><loc>{SITE_URL}/{q['url']}</loc></url>"
        for q in questions
    )
    save_text(SITEMAP_PATH,
f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml}
</urlset>""")

# =========================
# Main
# =========================
def main():
    subprocess.run(["python3","question_generator.py"],check=True)

    raw_questions = load_json(QUESTIONS_PATH)
    questions = [normalize(q, i) for i, q in enumerate(raw_questions)]

    if not questions:
        print("⚠ 質問を生成できませんでした")
        return

    cur=questions[-1]
    content=generate_article(cur["title"],cur["question"])
    summary=generate_summary(cur["title"],content)

    with open(POST_TEMPLATE_PATH,encoding="utf-8") as f:
        tpl=f.read()

    html=(tpl
        .replace("{{TITLE}}",esc(cur["title"]))
        .replace("{{DESCRIPTION}}",esc(summary))
        .replace("{{CONTENT}}",content)
        .replace("{{RELATED}}",internal_links(cur,questions))
        .replace("{{CANONICAL}}",canonical(cur["slug"]))
        .replace("{{AUTHOR}}",author_schema())
        .replace("{{ARTICLE_SCHEMA}}",article_schema(cur["title"],summary,cur["slug"]))
        .replace("{{FAQ}}",faq_schema_multi(cur["title"],cur["question"]))
        .replace("{{GOOGLE_VERIFY}}",
                 f'<meta name="google-site-verification" content="{GOOGLE_VERIFICATION}" />')
    )

    save_text(os.path.join(POST_DIR,f"{cur['slug']}.html"),html)
    generate_sitemap(questions)

    print("✅ AI要約・Search Console 完全対応生成完了")

if __name__=="__main__":
    main()
