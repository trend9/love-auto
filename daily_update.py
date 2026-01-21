import os
import json
import re
import random
from datetime import datetime
from llama_cpp import Llama

# =========================
# パス
# =========================
MODEL_PATH = "./models/model.gguf"
POST_DIR = "posts"
DATA_DIR = "data"
JSON_PATH = "data/questions.json"
ARCHIVE_PATH = "archive.html"
INDEX_PATH = "index.html"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# LLM
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.7,
)

# =========================
# 既存データ読込
# =========================
data = []
used_titles = set()

if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        used_titles = {d["title"] for d in data}

# =========================
# テーマ自動生成（被り防止）
# =========================
themes = [
    "結婚の焦り",
    "年齢と恋愛の不安",
    "周囲と比べてしまう恋",
    "将来が見えない交際",
    "一人で生きる覚悟"
]

available = [t for t in themes if t not in used_titles]
theme = random.choice(available if available else themes)

# =========================
# プロンプト
# =========================
PROMPT = f"""
あなたは35歳の日本人女性「結姉さん」です。
以下の形式のみで、日本語で出力してください。
説明・英語・署名は禁止。

1.ラジオネーム：
2.お便り内容：（情景が浮かぶ具体的な悩み）
3.結姉さんの回答：（100〜200文字）
4.メタディスクリプション：（100文字前後）

【テーマ】
{theme}
"""

# =========================
# extract（ゆるめ）
# =========================
def extract(label, text):
    m = re.search(rf"{label}[:：]\s*(.*?)(?=\n\d\.|$)", text, re.S)
    return m.group(1).strip() if m else ""

# =========================
# AI生成（最大3回）
# =========================
for _ in range(3):
    result = llm(PROMPT, max_tokens=900)
    out = result["choices"][0]["text"]

    name = extract("1.ラジオネーム", out)
    letter = extract("2.お便り内容", out)
    answer = extract("3.結姉さんの回答", out)
    meta = extract("4.メタディスクリプション", out)

    if all([name, letter, answer, meta]):
        break
else:
    raise RuntimeError("AI生成失敗")

# =========================
# 日付・URL
# =========================
now = datetime.now()
slug = now.strftime("%Y%m%d_%H%M%S")
date_str = now.strftime("%Y/%m/%d %H:%M")
post_url = f"posts/{slug}.html"

# =========================
# HTML生成
# =========================
with open("post_template.html", "r", encoding="utf-8") as f:
    html = f.read()

html = (
    html.replace("{{TITLE}}", theme)
        .replace("{{DATE}}", date_str)
        .replace("{{NAME}}", name)
        .replace("{{LETTER}}", letter)
        .replace("{{ANSWER}}", answer)
        .replace("{{META}}", meta)
)

with open(post_url, "w", encoding="utf-8") as f:
    f.write(html)

# =========================
# JSON更新
# =========================
entry = {
    "title": theme,
    "url": post_url,
    "date": date_str,
    "description": meta
}

data.insert(0, entry)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# archive.html 自動生成
# =========================
archive_items = "\n".join(
    f'<li><a href="{d["url"]}">{d["title"]}</a> <span>{d["date"]}</span></li>'
    for d in data
)

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html lang="ja">
<meta charset="UTF-8">
<title>恋愛相談アーカイブ</title>
<body>
<h1>相談アーカイブ</h1>
<ul>
{archive_items}
</ul>
<a href="index.html">トップへ戻る</a>
</body>
</html>
""")

# =================
