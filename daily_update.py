#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
POST_DIR = BASE_DIR / "posts"

QUESTION_FILE = DATA_DIR / "questions.json"
TEMPLATE_PATH = BASE_DIR / "post_template.html"
MODEL_PATH = BASE_DIR / "models" / "model.gguf"

POST_DIR.mkdir(exist_ok=True)

# =========================
# Utils
# =========================

def now():
    return datetime.now()

def iso(dt):
    return dt.isoformat()

def jp(dt):
    return dt.strftime("%Y年%m月%d日")

def slugify(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:50] or "love-consulting"

def safe(text):
    return text.strip() if text else ""

# =========================
# LLM
# =========================

llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=2048,
    temperature=0.8,
    verbose=False
)

PROMPT = """
以下の恋愛相談に対して、SEOを意識した日本語記事を作成してください。

【必須出力形式（厳守）】
タイトル：
要約：
結論：
相手の心理：
具体的な行動：
- 行動1
- 行動2
- 行動3
避けたい行動：
- NG1
- NG2
よくある勘違い：
まとめ：

※ 抽象論禁止
※ 600文字以上
"""

def extract(label, text):
    if label not in text:
        return ""
    part = text.split(label, 1)[1]
    return part.split("\n", 1)[1].strip()

def list_items(block):
    return "".join(
        f"<li>{line.lstrip('-').strip()}</li>"
        for line in block.splitlines()
        if line.strip().startswith("-")
    )

# =========================
# Main
# =========================

def main():
    print("=== daily_update START ===")

    if not QUESTION_FILE.exists():
        print("questions.json not found")
        return

    questions = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
    q = next((x for x in questions if not x.get("used")), None)

    if not q:
        print("No unused questions")
        return

    prompt = PROMPT + "\n【相談内容】\n" + q["question"]

    try:
        res = llm(prompt, max_tokens=1600)
        out = res["choices"][0]["text"]
    except Exception as e:
        print("LLM error:", e)
        return

    if "タイトル：" not in out:
        print("Invalid LLM output")
        return

    title = safe(extract("タイトル：", out))
    lead = safe(extract("要約：", out))
    conclusion = safe(extract("結論：", out))
    psychology = safe(extract("相手の心理：", out))
    action = extract("具体的な行動：", out)
    ng = extract("避けたい行動：", out)
    misunderstanding = safe(extract("よくある勘違い：", out))
    summary = safe(extract("まとめ：", out))

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
    q["used_at"] = iso(today)
    q["title"] = title
    q["description"] = lead[:120]
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
