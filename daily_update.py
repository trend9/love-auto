import os
import json
import re
from datetime import datetime
import random

# =====================
# 設定
# =====================
DATA_PATH = "data/questions.json"
POST_DIR = "posts"
TEMPLATE_PATH = "post_template.html"

SITE_URL = "https://trend9.github.io/love-auto"
IMAGE_URL = f"{SITE_URL}/yui.png"
AUTHOR_NAME = "結姉さん"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# =====================
# ユーティリティ
# =====================
def clean_text(text: str, max_len: int) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(出力|回答例|import .*|print\(.*?\))", "", text)
    return text.strip()[:max_len]

def safe_fallback_title(name: str) -> str:
    return f"{name}さんの悩み相談"

def now_strings():
    dt = datetime.now()
    return (
        dt.strftime("%Y/%m/%d %H:%M"),
        dt.strftime("%Y%m%d_%H%M%S"),
        dt.isoformat()
    )

def load_questions():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_questions(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# ダミー入力（※ここは既存ロジックに差し替え可）
# =====================
NAMES = ["Kazuki", "Haruka", "Mina", "Yui", "Sakura"]

name = random.choice(NAMES)
letter = (
    "私は大学生で、将来のキャリアについて悩んでいます。\n"
    "今やっていることが本当に将来に繋がるのか、不安になります。"
)
answer = (
    "大学生の段階で将来に不安を感じるのは、とても自然なことです。\n"
    "今は「決めきる」よりも「試す」時期だと考えてください。\n"
    "経験の積み重ねが、後から意味を持つことも多いですよ。"
)

# =====================
# タイトル & メタ生成
# =====================
raw_title = f"{name}さんからのお便り"
raw_meta = clean_text(letter, 120)

title = clean_text(raw_title, 50)
meta = clean_text(raw_meta, 120)

if not title:
    title = safe_fallback_title(name)

if not meta:
    meta = clean_text(letter, 120)

# =====================
# 日付・URL
# =====================
date_str, slug, iso_date = now_strings()
post_filename = f"{slug}.html"
post_path = os.path.join(POST_DIR, post_filename)
post_url = f"{SITE_URL}/posts/{post_filename}"

# =====================
# JSON-LD
# =====================
json_ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": meta,
    "datePublished": iso_date,
    "author": {
        "@type": "Person",
        "name": AUTHOR_NAME
    },
    "image": IMAGE_URL,
    "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": post_url
    }
}

json_ld_html = (
    '<script type="application/ld+json">\n'
    + json.dumps(json_ld, ensure_ascii=False)
    + '\n</script>'
)

# =====================
# RELATED 生成
# =====================
questions = load_questions()

related_items = []
for q in reversed(questions[-5:]):
    rt = clean_text(q.get("title", ""), 40)
    if rt:
        related_items.append(
            f'<li><a href="../{q["url"]}">{rt}</a></li>'
        )

related_html = "\n".join(related_items) if related_items else ""

# =====================
# HTML生成
# =====================
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = f.read()

html = (
    template
    .replace("{{TITLE}}", title)
    .replace("{{META}}", meta)
    .replace("{{NAME}}", name)
    .replace("{{DATE}}", date_str)
    .replace("{{LETTER}}", letter)
    .replace("{{ANSWER}}", answer)
    .replace("{{RELATED}}", related_html)
    .replace("{{JSON_LD}}", json_ld_html)
)

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)

# =====================
# questions.json 永久追記
# =====================
questions.append({
    "title": title,
    "url": f"posts/{post_filename}",
    "date": date_str,
    "description": meta
})

save_questions(questions)

print(f"✔ Generated: {post_path}")
