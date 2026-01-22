import os
import json
import datetime
from pathlib import Path
import html
import re

BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / "posts"
DATA_DIR = BASE_DIR / "data"
QUESTIONS_JSON = DATA_DIR / "questions.json"
POST_TEMPLATE = BASE_DIR / "post_template.html"

POSTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# -----------------------
# ユーティリティ
# -----------------------

def now_jst():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def safe_text(s: str) -> str:
    if not s:
        return ""
    return html.escape(s.strip())

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def summarize_for_title(text: str, max_len=32):
    text = re.sub(r"\s+", " ", text)
    return text[:max_len] if len(text) > max_len else text

def summarize_for_description(text: str, max_len=110):
    text = re.sub(r"\s+", " ", text)
    return text[:max_len] if len(text) > max_len else text

def is_bad_meta(text: str) -> bool:
    if not text:
        return True
    if len(text.strip()) < 6:
        return True
    if text.strip() in ["相談", "相談相談"]:
        return True
    return False

# -----------------------
# 永久蓄積JSONの読み込み
# -----------------------

if QUESTIONS_JSON.exists():
    with open(QUESTIONS_JSON, "r", encoding="utf-8") as f:
        questions = json.load(f)
else:
    questions = []

# -----------------------
# 相談生成（※ここは既存生成物を使う前提）
# -----------------------
# ここでは「すでに生成済みの相談・回答が入ってくる」前提
# 実運用ではこの部分がAI生成に差し替わる

letter_text = normalize_whitespace("""
私は大学生で、将来のキャリアについて悩んでいます。
今やっていることが本当に将来に繋がるのか、不安になります。
""")

answer_text = normalize_whitespace("""
大学生の段階で将来に不安を感じるのは、とても自然なことです。
今は「決めきる」よりも「試す」時期だと考えてください。
経験の積み重ねが、後から意味を持つことも多いですよ。
""")

sender_name = "Kazuki"

# -----------------------
# メタ生成（失敗防止）
# -----------------------

raw_title = f"{sender_name}さんからのお便り"
raw_description = letter_text

title = summarize_for_title(raw_title, 32)
description = summarize_for_description(raw_description, 110)

if is_bad_meta(title):
    title = summarize_for_title(letter_text, 32)

if is_bad_meta(description):
    description = summarize_for_description(letter_text, 110)

# -----------------------
# ファイル名生成
# -----------------------

dt = now_jst()
slug = dt.strftime("%Y%m%d_%H%M%S")
post_filename = f"{slug}.html"
post_path = POSTS_DIR / post_filename
post_url = f"posts/{post_filename}"

# -----------------------
# 関連記事生成
# -----------------------

related_items = []
for q in reversed(questions[-5:]):
    related_items.append(
        f'<li><a href="../{q["url"]}">{html.escape(q["title"])}</a></li>'
    )

if not related_items:
    related_html = "<li>現在、関連する相談はありません</li>"
else:
    related_html = "\n".join(related_items)

# -----------------------
# JSON-LD
# -----------------------

json_ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": description,
    "datePublished": dt.isoformat(),
    "author": {
        "@type": "Person",
        "name": "結姉さん"
    },
    "image": "https://trend9.github.io/love-auto/yui.png",
    "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": f"https://trend9.github.io/love-auto/{post_url}"
    }
}

# -----------------------
# HTML生成
# -----------------------

with open(POST_TEMPLATE, "r", encoding="utf-8") as f:
    template = f.read()

html_content = template
html_content = html_content.replace("{{TITLE}}", safe_text(title))
html_content = html_content.replace("{{DESCRIPTION}}", safe_text(description))
html_content = html_content.replace("{{DATE}}", dt.strftime("%Y/%m/%d %H:%M"))
html_content = html_content.replace("{{SENDER}}", safe_text(sender_name))
html_content = html_content.replace("{{LETTER}}", safe_text(letter_text))
html_content = html_content.replace("{{ANSWER}}", safe_text(answer_text))
html_content = html_content.replace("{{RELATED}}", related_html)
html_content = html_content.replace(
    "{{JSON_LD}}",
    json.dumps(json_ld, ensure_ascii=False)
)

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html_content)

# -----------------------
# questions.json 追記（削除しない）
# -----------------------

questions.append({
    "title": title,
    "url": post_url,
    "date": dt.strftime("%Y/%m/%d %H:%M"),
    "description": description
})

with open(QUESTIONS_JSON, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print("✅ daily_update.py completed successfully")
