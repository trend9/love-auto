import json
import os
from datetime import datetime
from pathlib import Path
import requests
import html
import random
import subprocess

subprocess.run(["python3", "question_generator.py"], check=True)

# ======================
# 設定
# ======================
BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / "posts"
DATA_DIR = BASE_DIR / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
ARCHIVE_FILE = BASE_DIR / "archive.html"
INDEX_FILE = BASE_DIR / "index.html"
POST_TEMPLATE_FILE = BASE_DIR / "post_template.html"

SITE_URL = "https://trend9.github.io/love-auto"
OG_IMAGE = f"{SITE_URL}/yui.png"

POSTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ======================
# 安全ユーティリティ
# ======================
def safe_text(s: str) -> str:
    return html.escape(s.strip())

def now_jst():
    return datetime.now().strftime("%Y/%m/%d %H:%M")

def now_iso():
    return datetime.now().isoformat()

def load_questions():
    if not QUESTIONS_FILE.exists():
        return []
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_questions(data):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ======================
# 相談データ（LLM不使用・安定）
# ======================
CONSULTATION_POOL = [
    {
        "name": "Kazuki",
        "letter": "私は大学生で、将来のキャリアについて悩んでいます。\n今やっていることが本当に将来に繋がるのか、不安になります。",
        "answer": "大学生の段階で将来に不安を感じるのは、とても自然なことです。\n今は「決めきる」よりも「試す」時期だと考えてください。\n経験の積み重ねは、後から必ず意味を持ちます。"
    },
    {
        "name": "Mika",
        "letter": "恋人との将来が見えず、不安になることがあります。\nこのまま続けていいのか悩んでいます。",
        "answer": "将来が見えないと不安になりますよね。\n一度、今の関係で大切にしたいことを書き出してみてください。\n答えは、行動の中で少しずつ見えてきます。"
    }
]

# ======================
# メイン生成
# ======================
def main():
    questions = load_questions()

    source = random.choice(CONSULTATION_POOL)
    name = safe_text(source["name"])
    letter = safe_text(source["letter"])
    answer = safe_text(source["answer"])

    title = f"{name}さんからのお便り"
    description = letter.split("\n")[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    post_filename = f"{timestamp}.html"
    post_path = POSTS_DIR / post_filename
    post_url = f"posts/{post_filename}"

    # ----------------------
    # related 安定生成（完全ガード版）
    # ----------------------
    related_items = ""
    if questions:
        for q in questions[-3:]:

            # id が無ければスキップ（壊れた古い質問）
            if "id" not in q:
                continue

            # url が無ければ自動補完
            if "url" not in q:
                q["url"] = f'posts/{q["id"]}.html'

            related_items += f'<li><a href="../{q["url"]}">{safe_text(q["title"])}</a></li>\n'


    # ----------------------
    # 記事HTML生成
    # ----------------------
    with open(POST_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        tpl = f.read()

    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": now_iso(),
        "author": {
            "@type": "Person",
            "name": "結姉さん"
        },
        "image": OG_IMAGE,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{SITE_URL}/{post_url}"
        }
    }

    json_ld_script = (
        '<script type="application/ld+json">'
        + json.dumps(json_ld, ensure_ascii=False)
        + '</script>'
    )

    html_content = tpl
    html_content = html_content.replace("{{TITLE}}", title)
    html_content = html_content.replace("{{META}}", description)
    html_content = html_content.replace("{{DATE}}", now_jst())
    html_content = html_content.replace("{{NAME}}", name)
    html_content = html_content.replace("{{LETTER}}", letter)
    html_content = html_content.replace("{{ANSWER}}", answer)
    html_content = html_content.replace("{{RELATED}}", related_items)
    html_content = html_content.replace("{{JSON_LD}}", json_ld_script)

    with open(post_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ----------------------
    # questions.json 永久追加
    # ----------------------
    questions.append({
        "title": title,
        "url": post_url,
        "date": now_jst(),
        "description": description
    })
    save_questions(questions)

    # ----------------------
    # archive.html 再生成（完全防御版）
    # ----------------------
    archive_list = ""

    for q in reversed(questions):

        # id が無いものは壊れた質問なのでスキップ
        if "id" not in q:
            continue

        # title が無い場合もスキップ（保険）
        if "title" not in q:
            continue

        # url が無ければここで必ず生成
        if "url" not in q:
            q["url"] = f'posts/{q["id"]}.html'

        archive_list += (
            f'<li>'
            f'<a href="{q["url"]}">{safe_text(q["title"])}</a>'
            f'</li>\n'
        )


    archive_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>相談アーカイブ</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>相談アーカイブ</h1>
<ul>
{archive_list}
</ul>
<a href="index.html">← トップへ戻る</a>
</body>
</html>
"""
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        f.write(archive_html)

    print("Daily update completed successfully.")

# ======================
if __name__ == "__main__":
    main()
