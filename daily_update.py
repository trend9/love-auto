import json
import os
from datetime import datetime
from llama_cpp import Llama
import html
import random

# ========= 設定 =========
MODEL_PATH = "models/model.gguf"
POST_DIR = "posts"
DATA_PATH = "data/questions.json"
TEMPLATE_PATH = "post_template.html"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ========= 安全ユーティリティ =========
def clean_text(text: str) -> str:
    text = html.escape(text.strip())
    return text.replace("\n\n\n", "\n\n")

def safe_json_load(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# ========= LLM =========
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1,
)

prompt = """
あなたは日本語の恋愛相談記事を生成します。

以下のJSON形式でのみ出力してください。
余計な説明・コード・プロンプト文は一切含めないでください。

{
  "name": "日本人の女性ラジオネーム（2〜4文字）",
  "title": "検索向けの自然な記事タイトル",
  "description": "120文字以内の要約メタディスクリプション",
  "letter": "相談本文（自然で一貫性のある内容）",
  "answer": "結姉さんとしての丁寧で具体的な回答"
}
"""

result = llm(prompt, max_tokens=900)
raw = result["choices"][0]["text"].strip()

try:
    data = json.loads(raw)
except Exception as e:
    raise RuntimeError("LLM JSON parse failed") from e

# ========= 整形 =========
name = clean_text(data["name"])
title = clean_text(data["title"])
description = clean_text(data["description"])
letter = clean_text(data["letter"])
answer = clean_text(data["answer"])

now = datetime.now()
slug = now.strftime("%Y%m%d_%H%M%S")
post_file = f"{POST_DIR}/{slug}.html"
url = f"posts/{slug}.html"

# ========= questions.json 永久追加 =========
questions = safe_json_load(DATA_PATH, [])

questions.append({
    "title": title,
    "url": url,
    "date": now.strftime("%Y/%m/%d %H:%M"),
    "description": description
})

with open(DATA_PATH, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

# ========= 関連記事 =========
related_items = [
    f'<li><a href="../{q["url"]}">{html.escape(q["title"])}</a></li>'
    for q in questions[:-1][-3:]
]
related_html = "\n".join(related_items)

# ========= テンプレ反映 =========
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    tpl = f.read()

json_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title,
    "description": description,
    "datePublished": now.isoformat(),
    "author": {"@type": "Person", "name": "結姉さん"},
    "image": "https://trend9.github.io/love-auto/yui.png",
    "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": f"https://trend9.github.io/love-auto/{url}"
    }
}, ensure_ascii=False)

html_out = tpl \
    .replace("{{TITLE}}", title) \
    .replace("{{META}}", description) \
    .replace("{{DATE}}", now.strftime("%Y/%m/%d %H:%M")) \
    .replace("{{NAME}}", name) \
    .replace("{{LETTER}}", letter) \
    .replace("{{ANSWER}}", answer) \
    .replace("{{RELATED}}", related_html) \
    .replace("{{JSONLD}}", json_ld)

with open(post_file, "w", encoding="utf-8") as f:
    f.write(html_out)

print("Generated:", post_file)
