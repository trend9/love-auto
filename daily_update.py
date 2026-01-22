import json
import os
import re
import html
from datetime import datetime
from pathlib import Path
from llama_cpp import Llama

# =========================
# パス設定
# =========================
BASE_DIR = Path(__file__).parent
POSTS_DIR = BASE_DIR / "posts"
DATA_DIR = BASE_DIR / "data"
QUESTIONS_JSON = DATA_DIR / "questions.json"
TEMPLATE_PATH = BASE_DIR / "post_template.html"

POSTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# =========================
# LLM 初期化
# =========================
llm = Llama(
    model_path=str(BASE_DIR / "models" / "model.gguf"),
    n_ctx=1024,
    temperature=0.7,
)

# =========================
# プロンプト（JSON風テキスト生成）
# =========================
PROMPT = """
以下の項目を日本語で作成してください。
JSONやコードは書かず、項目名も書かないでください。

タイトル：
ラジオネーム：
相談文：
回答文：
メタディスクリプション：
"""

response = llm(PROMPT, max_tokens=900)
text = response["choices"][0]["text"]

# =========================
# 強制抽出（JSON不使用）
# =========================
def extract(label, text):
    pattern = rf"{label}：(.*?)(?=\n\S+：|\Z)"
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else ""

title = extract("タイトル", text)
radio_name = extract("ラジオネーム", text)
letter = extract("相談文", text)
answer = extract("回答文", text)
meta = extract("メタディスクリプション", text)

# =========================
# サニタイズ
# =========================
def clean(s):
    return html.escape(
        s.replace("\r", "")
         .replace("\n", "<br>")
         .strip()
    )

title = clean(title)[:60]
radio_name = clean(radio_name)[:10]
letter = clean(letter)
answer = clean(answer)
meta = clean(meta)[:120]

# =========================
# 日付・URL
# =========================
now = datetime.now()
date_str = now.strftime("%Y/%m/%d %H:%M")
slug = now.strftime("%Y%m%d_%H%M%S")
filename = f"{slug}.html"
url = f"posts/{filename}"

# =========================
# JSON-LD
# =========================
json_ld = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": meta,
    "datePublished": now.isoformat(),
    "author": {
        "@type": "Person",
        "name": "結姉さん"
    },
    "image": "https://trend9.github.io/love-auto/yui.png",
    "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": f"https://trend9.github.io/love-auto/{url}"
    }
}

# =========================
# HTML生成
# =========================
template = TEMPLATE_PATH.read_text(encoding="utf-8")

html_out = (
    template
    .replace("{{TITLE}}", title)
    .replace("{{META}}", meta)
    .replace("{{DATE}}", date_str)
    .replace("{{NAME}}", radio_name)
    .replace("{{LETTER}}", letter)
    .replace("{{ANSWER}}", answer)
    .replace(
        "{{JSON_LD}}",
        f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'
    )
)

(POSTS_DIR / filename).write_text(html_out, encoding="utf-8")

# =========================
# questions.json 永久蓄積
# =========================
if QUESTIONS_JSON.exists():
    questions = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
else:
    questions = []

if not any(q["url"] == url for q in questions):
    questions.insert(0, {
        "title": title,
        "url": url,
        "date": date_str,
        "description": meta
    })

QUESTIONS_JSON.write_text(
    json.dumps(questions, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("✅ Generated:", filename)
