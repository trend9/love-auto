#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from datetime import datetime
from llama_cpp import Llama

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
POST_DIR = BASE_DIR / "posts"

QUESTION_FILE = DATA_DIR / "questions.json"
TEMPLATE_PATH = BASE_DIR / "post_template.html"
MODEL_PATH = BASE_DIR / "models" / "model.gguf"

POST_DIR.mkdir(exist_ok=True)

def now():
    return datetime.now()

def iso(dt):
    return dt.isoformat()

def jp(dt):
    return dt.strftime("%Y年%m月%d日")

def slugify(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:50] or "love-consulting"

def safe(v, fallback=""):
    return v.strip() if isinstance(v, str) and v.strip() else fallback

llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=2048,
    temperature=0.8,
    verbose=False
)

PROMPT = """
以下の恋愛相談に対して、恋愛相談記事を書いてください。

出力は自然文でOKです。
"""

def extract(label, text):
    if label in text:
        return text.split(label, 1)[1].split("\n", 1)[0].strip()
    return ""

def list_items(text):
    items = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("-"):
            items.append(f"<li>{line.lstrip('-').strip()}</li>")
    return "".join(items)

def main():
    print("=== daily_update START ===")

    questions = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
    q = next((x for x in questions if not x.get("used")), None)

    if not q:
        print("No unused questions")
        return

    try:
        res = llm(q["question"], max_tokens=1600)
        out = res["choices"][0]["text"]
    except Exception as e:
        print("LLM error:", e)
        return

    # 🔥 フォールバック前提で組み立てる
    title = extract("タイトル", out)
    if not title:
        title = q["question"][:32] + "の悩みについて"

    lead = extract("要約", out) or out[:120]
    conclusion = extract("結論", out) or "まずは相手との距離を少しずつ縮めることが大切です。"
    psychology = extract("心理", out) or out[:200]
    action = extract("行動", out)
    ng = extract("避け", out)
    misunderstanding = extract("勘違い", out) or ""
    summary = extract("まとめ", out) or conclusion

    today = now()
    slug = slugify(title)
    filename = f"{today.strftime('%Y-%m-%d')}-{slug}.html"
    url = f"posts/{filename}"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    html = (
        template
        .replace("{{TITLE}}", title)
        .replace("{{META_DESCRIPTION}}", lead[:120])
        .replace("{{DATE_ISO}}", iso(today))
        .replace("{{DATE_JP}}", jp(today))
        .replace("{{PAGE_URL}}", url)
        .replace("{{CANONICAL}}", f'<link rel="canonical" href="{url}">')
        .replace("{{LEAD}}", lead)
        .replace("{{QUESTION}}", q["question"])
        .replace("{{SUMMARY_ANSWER}}", conclusion)
        .replace("{{PSYCHOLOGY}}", psychology)
        .replace("{{ACTION_LIST}}", list_items(action))
        .replace("{{NG_LIST}}", list_items(ng))
        .replace("{{MISUNDERSTANDING}}", misunderstanding)
        .replace("{{CONCLUSION}}", summary)
        .replace("{{RELATED}}", "")
        .replace("{{PREV}}", "")
        .replace("{{NEXT}}", "")
        .replace("{{FAQ}}", "")
    )

    (POST_DIR / filename).write_text(html, encoding="utf-8")

    q["used"] = True
    q["title"] = title
    q["url"] = url
    q["date"] = jp(today)

    QUESTION_FILE.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✔ HTML generated:", filename)
    print("=== daily_update END ===")

if __name__ == "__main__":
    main()
