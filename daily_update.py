import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

# ======================
# 基本設定
# ======================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
POSTS_DIR = os.path.join(ROOT_DIR, "posts")

QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

JST = timezone(timedelta(hours=9))

# ======================
# ユーティリティ
# ======================
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_questions(data):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_llm(prompt, retry=3):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a professional Japanese consulting writer."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    for i in range(retry):
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        if text:
            return text
        time.sleep(1)

    raise RuntimeError("LLM returned empty response")

def parse_llm_json(text, retry_prompt):
    try:
        return json.loads(text)
    except Exception:
        # JSON崩壊時は再生成
        fixed = call_llm(retry_prompt)
        return json.loads(fixed)

# ======================
# プロンプト
# ======================
BASE_PROMPT = """
あなたは日本語の人生・恋愛相談コラムの執筆AIです。

以下の条件を必ず守ってください。

・出力は必ずJSONのみ
・JSON以外の文字を一切出力しない
・すべての項目は空文字不可
・相談文と回答は必ず同じ前提（年齢・立場）を共有する
・回答文では相談文に含まれる具体語を2つ以上必ず使う

以下のJSONテンプレートを完全に埋めてください。

{
  "name": "",
  "title": "",
  "description": "",
  "letter": "",
  "answer": ""
}
"""

RETRY_PROMPT = """
前回の出力はJSONとして不正でした。
必ず以下のJSONテンプレートのみを出力してください。

{
  "name": "",
  "title": "",
  "description": "",
  "letter": "",
  "answer": ""
}
"""

# ======================
# メイン処理
# ======================
questions = load_questions()

raw = call_llm(BASE_PROMPT)
data = parse_llm_json(raw, RETRY_PROMPT)

now = datetime.now(JST)
slug = now.strftime("%Y%m%d_%H%M%S")
filename = f"{slug}.html"
post_path = os.path.join(POSTS_DIR, filename)

questions.append({
    "slug": slug,
    "name": data["name"],
    "title": data["title"],
    "description": data["description"],
})

save_questions(questions)

# ======================
# HTML生成
# ======================
json_ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": data["title"],
    "description": data["description"],
    "datePublished": now.isoformat(),
    "author": {
        "@type": "Person",
        "name": "結姉さん"
    },
    "image": "https://trend9.github.io/love-auto/yui.png",
    "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": f"https://trend9.github.io/love-auto/posts/{filename}"
    }
}

html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{data["title"]}</title>
<meta name="description" content="{data["description"]}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="post-container">
<p class="post-date">更新日：{now.strftime("%Y/%m/%d %H:%M")}</p>

<h1 class="post-title">{data["name"]}さんからのお便り</h1>

<section>
<h2>お便り内容</h2>
<p style="white-space:pre-wrap;">{data["letter"]}</p>
</section>

<section>
<h2>結姉さんからの回答</h2>
<p style="white-space:pre-wrap;">{data["answer"]}</p>
</section>

<div class="back-area">
<a href="../index.html">← 相談室のトップへ戻る</a>
</div>
</div>
</body>
</html>
"""

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated: {post_path}")
