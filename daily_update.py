import json
import os
import random
import time
from datetime import datetime
from llama_cpp import Llama

# =========================
# 基本設定
# =========================
MODEL_PATH = "./models/model.gguf"
POST_DIR = "posts"
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "questions.json")
POST_TEMPLATE = "post_template.html"
INDEX_PATH = "index.html"
ARCHIVE_PATH = "archive.html"

MAX_RETRY = 3

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# LLM 初期化
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=os.cpu_count(),
    chat_format="llama-3"
)

# =========================
# 既存データ読み込み
# =========================
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
else:
    questions = []

used_titles = {q["title"] for q in questions if q.get("title")}

# =========================
# テーマ自動生成（被り防止）
# =========================
THEMES = [
    "結婚の焦り",
    "周囲と比べてしまう恋",
    "年齢への不安",
    "片思いが長すぎる悩み",
    "復縁したい気持ち",
    "好きだけど進めない関係",
]

random.shuffle(THEMES)

theme = None
for t in THEMES:
    if t not in used_titles:
        theme = t
        break

if theme is None:
    theme = random.choice(THEMES)

# =========================
# プロンプト
# =========================
PROMPT = f"""
あなたは35歳の恋愛相談ラジオパーソナリティ「結姉さん」です。

以下の形式を厳守してください。
JSONや記号は出力せず、文章のみで生成してください。

【ラジオネーム】
日本人女性らしい、親しみやすい名前

【SEOタイトル】
検索キーワードを含む自然な日本語タイトル

【相談文】
テーマ「{theme}」に基づいた具体的な恋愛相談（情景が浮かぶ文章）

【回答文】
結姉さんとして寄り添いと解決案を提示する100〜200文字

【メタディスクリプション】
100文字前後の要約
"""

# =========================
# AI生成（リトライあり）
# =========================
def generate_text():
    for _ in range(MAX_RETRY):
        output = llm(
            PROMPT,
            max_tokens=900,
            temperature=0.7,
        )

        choice = output["choices"][0]

        if "message" in choice and "content" in choice["message"]:
            text = choice["message"]["content"].strip()
        else:
            text = choice.get("text", "").strip()

        if text:
            return text

        time.sleep(1)

    raise RuntimeError("AI生成失敗")

text = generate_text()

# =========================
# パース（ゆるめ）
# =========================
def extract(label):
    for line in text.splitlines():
        if line.startswith(label):
            return line.replace(label, "").strip()
    return ""

radio_name = extract("【ラジオネーム】")
title = extract("【SEOタイトル】")
consult = extract("【相談文】")
answer = extract("【回答文】")
meta = extract("【メタディスクリプション】")

# フォールバック
if not title:
    title = theme

# =========================
# 日付・パス生成
# =========================
now = datetime.now()
timestamp = now.strftime("%Y%m%d_%H%M%S")
date_str = now.strftime("%Y/%m/%d %H:%M")

url = f"posts/{timestamp}.html"
post_path = os.path.join(POST_DIR, f"{timestamp}.html")

# =========================
# HTML生成
# =========================
with open(POST_TEMPLATE, "r", encoding="utf-8") as f:
    template = f.read()

html = template \
    .replace("{{title}}", title) \
    .replace("{{radio_name}}", radio_name) \
    .replace("{{date}}", date_str) \
    .replace("{{consult}}", consult) \
    .replace("{{answer}}", answer) \
    .replace("{{meta}}", meta)

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)

# =========================
# JSON更新（先頭追加）
# =========================
questions.insert(0, {
    "title": title,
    "url": url,
    "date": date_str,
    "description": meta
})

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

# =========================
# index.html 更新（最新5件）
# =========================
def build_list(items):
    return "\n".join(
        f'<li><a href="{q["url"]}">{q["title"]}</a><span>{q["date"]}</span></li>'
        for q in items
    )

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    index_html = f.read()

index_html = index_html.replace(
    "<!-- LATEST_POSTS -->",
    build_list(questions[:5])
)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(index_html)

# =========================
# archive.html 自動生成
# =========================
archive_items = build_list(questions)

archive_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>過去の相談一覧</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>過去の恋愛相談</h1>
<ul>
{archive_items}
</ul>
<a href="index.html">トップへ戻る</a>
</body>
</html>
"""

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(archive_html)

print("✅ 記事生成・更新 完了")
