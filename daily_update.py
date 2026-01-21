import json
import os
from datetime import datetime
from pathlib import Path
from llama_cpp import Llama
import html

# =========================
# 設定
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
# LLMプロンプト（JSON ONLY）
# =========================
PROMPT = """
あなたは日本の恋愛相談ラジオの原稿作成AIです。

以下の形式の【JSONのみ】を出力してください。
説明文・前置き・コード・Markdownは禁止です。

{
  "title": "30文字以内の自然な日本語タイトル",
  "radio_name": "女性のラジオネーム（2〜4文字、日本語）",
  "letter": "相談文（300〜500文字、日本語）",
  "answer": "結姉さんの回答（400〜700文字、日本語）",
  "meta": "120文字以内の自然なメタディスクリプション"
}
"""

# =========================
# LLM実行
# =========================
response = llm(
    PROMPT,
    max_tokens=900,
)

raw = response["choices"][0]["text"].strip()

# JSONだけを厳密に抽出
start = raw.find("{")
end = raw.rfind("}") + 1
json_text = raw[start:end]

try:
    data = json.loads(json_text)
except Exception as e:
    raise RuntimeError("LLM JSON parse failed") from e

# =========================
# 値のサニタイズ
# =========================
def clean(text: str) -> str:
    return html.escape(text.strip())

title = clean(data["title"])
radio_name = clean(data["radio_name"])
letter = clean(data["letter"])
answer = clean(data["answer"])
meta = clean(data["meta"])

now = datetime.now()
date_str = now.strftime("%Y/%m/%d %H:%M")
slug = now.strftime("%Y%m%d_%H%M%S")
filename = f"{slug}.html"
post_path = POSTS_DIR / filename
url = f"posts/{filename}"

# =========================
# JSON-LD（SEO）
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

html_out = template
html_out = html_out.replace("{{TITLE}}", title)
html_out = html_out.replace("{{META}}", meta)
html_out = html_out.replace("{{DATE}}", date_str)
html_out = html_out.replace("{{NAME}}", radio_name)
html_out = html_out.replace("{{LETTER}}", letter)
html_out = html_out.replace("{{ANSWER}}", answer)
html_out = html_out.replace(
    "{{JSON_LD}}",
    f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>'
)

post_path.write_text(html_out, encoding="utf-8")

# =========================
# questions.json 永久蓄積
# =========================
if QUESTIONS_JSON.exists():
    questions = json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))
else:
    questions = []

# URL重複防止
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

print("✅ Post generated:", filename)
