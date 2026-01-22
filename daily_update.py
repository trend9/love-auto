import os
import json
import subprocess
import datetime
import requests
from pathlib import Path
from html import escape

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
POSTS_DIR = BASE_DIR / "posts"

QUESTIONS_FILE = DATA_DIR / "questions.json"
USED_FILE = DATA_DIR / "used_questions.json"
ARCHIVE_FILE = BASE_DIR / "archive.html"
POST_TEMPLATE = BASE_DIR / "post_template.html"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL = "gpt-4o-mini"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ----------------------
# utility
# ----------------------
def safe(text):
    return escape(text)

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ----------------------
# GitHub Models call
# ----------------------
def github_llm(prompt: str) -> str:
    url = "https://models.inference.ai.azure.com/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "あなたは恋愛相談サイト『ゆい姉さんの恋愛相談室』の回答者です。"
                    "口調は優しく自然、日本語。"
                    "テンプレ感・箇条書き・定型文は禁止。"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 1200
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ----------------------
# main
# ----------------------
def main():
    # ① 質問生成（B）
    subprocess.run(["python3", "question_generator.py"], check=True)

    questions = load_json(QUESTIONS_FILE, [])
    used = load_json(USED_FILE, [])

    if not questions:
        print("⚠ 質問がありません")
        return

    q = questions.pop(0)
    used.append(q)

    save_json(QUESTIONS_FILE, questions)
    save_json(USED_FILE, used)

    title = q["title"]
    body = q["body"]

    # ② 記事生成（A）
    prompt = f"""
以下は読者からの恋愛相談です。

【相談内容】
{body}

これに対して、ゆい姉さんとして1ページの記事を書いてください。

条件：
・冒頭は3〜5行の自然な語り
・h2 を1つ以上使う
・h3 を使って具体的なアドバイスを深掘り
・テンプレ禁止
・SEOを意識しつつ人間味重視
"""

    article_html = github_llm(prompt)

    now = datetime.datetime.now()
    post_id = now.strftime("%Y%m%d_%H%M%S")
    post_path = POSTS_DIR / f"{post_id}.html"

    html = POST_TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("{{TITLE}}", safe(title))
    html = html.replace("{{CONTENT}}", article_html)
    html = html.replace("{{DATE}}", now.strftime("%Y/%m/%d %H:%M"))

    post_path.write_text(html, encoding="utf-8")

    q["url"] = f"posts/{post_id}.html"

    # ③ archive 再生成
    archive_items = ""
    for item in reversed(used):
        if "url" in item:
            archive_items += f'<li><a href="{item["url"]}">{safe(item["title"])}</a></li>\n'

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
{archive_items}
</ul>
</body>
</html>
"""

    ARCHIVE_FILE.write_text(archive_html, encoding="utf-8")

    print("✅ Daily update completed successfully.")

if __name__ == "__main__":
    main()
