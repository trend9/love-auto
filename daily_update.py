import os
import json
import time
import random
from datetime import datetime
from llama_cpp import Llama

# =====================
# パス設定
# =====================
MODEL_PATH = "./models/model.gguf"
POST_TEMPLATE = "post_template.html"
POST_DIR = "posts"
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "questions.json")
INDEX_PATH = "index.html"
ARCHIVE_PATH = "archive.html"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =====================
# LLM 初期化
# =====================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=os.cpu_count(),
    chat_format="llama-3"
)

# =====================
# JSON 読み込み
# =====================
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)
else:
    questions = []

used_titles = {q["title"] for q in questions if q.get("title")}

# =====================
# テーマ（被り防止）
# =====================
themes = [
    "結婚の焦り",
    "周囲と比べてしまう恋",
    "年齢への不安",
    "将来が見えない恋愛",
    "復縁を諦めきれない気持ち",
    "好きだけど進めない関係"
]

random.shuffle(themes)
theme = next((t for t in themes if t not in used_titles), random.choice(themes))

# =====================
# プロンプト
# =====================
PROMPT = f"""
あなたは35歳の恋愛相談ラジオのパーソナリティ「結姉さん」です。

以下をすべて生成してください。
記号やJSONは使わず、自然な日本語で書いてください。

【ラジオネーム】
【SEOタイトル】
【相談文】
【回答文】（100〜200文字）
【メタディスクリプション】（100文字前後）

テーマ：{theme}
"""

# =====================
# AI生成（リトライ）
# =====================
def generate():
    for _ in range(3):
        result = llm(PROMPT, max_tokens=900, temperature=0.7)
        choice = result["choices"][0]

        if "message" in choice and "content" in choice["message"]:
            text = choice["message"]["content"].strip()
        else:
            text = choice.get("text", "").strip()

        if text:
            return text

        time.sleep(1)

    raise RuntimeError("AI生成失敗")

raw = generate()

# =====================
# 正しい抽出（ブロック方式）
# =====================
def extract_block(label, text):
    lines = text.splitlines()
    collecting = False
    buffer = []

    for line in lines:
        if line.strip().startswith(label):
            collecting = True
            continue
        if collecting and line.strip().startswith("【"):
            break
        if collecting:
            buffer.append(line)

    return "\n".join(buffer).strip()

name = extract_block("【ラジオネーム】", raw)
title = extract_block("【SEOタイトル】", raw) or theme
letter = extract_block("【相談文】", raw)
answer = extract_block("【回答文】", raw)
meta = extract_block("【メタディスクリプション】", raw)

# =====================
# 日付・パス
# =====================
now = datetime.now()
timestamp = now.strftime("%Y%m%d_%H%M%S")
date_str = now.strftime("%Y/%m/%d %H:%M")

post_filename = f"{timestamp}.html"
post_path = os.path.join(POST_DIR, post_filename)
url = f"posts/{post_filename}"

# =====================
# HTML生成
# =====================
with open(POST_TEMPLATE, "r", encoding="utf-8") as f:
    template = f.read()

html = (
    template
    .replace("{{TITLE}}", title)
    .replace("{{META}}", meta)
    .replace("{{DATE}}", date_str)
    .replace("{{NAME}}", name)
    .replace("{{LETTER}}", letter)
    .replace("{{ANSWER}}", answer)
)

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)

# =====================
# JSON更新
# =====================
questions.insert(0, {
    "title": title,
    "url": url,
    "date": date_str,
    "description": meta
})

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

# =====================
# index 更新（既存仕様前提）
# =====================
def build_list(items):
    return "\n".join(
        f'<li><a href="{q["url"]}">{q["title"]}</a><span>{q["date"]}</span></li>'
        for q in items[:5]
    )

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    index_html = f.read()

index_html = index_html.replace("<!-- LATEST_POSTS -->", build_list(questions))

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(index_html)

# =====================
# archive.html 自動生成
# =====================
archive_items = "\n".join(
    f'<li><a href="{q["url"]}">{q["title"]}</a> <span>{q["date"]}</span></li>'
    for q in questions
)

archive_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>過去の恋愛相談一覧</title>
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

print("=== 記事生成・反映 完了 ===")
