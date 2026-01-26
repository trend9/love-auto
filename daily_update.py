#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from datetime import datetime
from llama_cpp import Llama

# =========================
# Path
# =========================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
POST_DIR = BASE_DIR / "posts"
TEMPLATE_PATH = BASE_DIR / "post_template.html"
QUESTION_FILE = DATA_DIR / "questions.json"
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
    return dt.strftime("%Y年%m月d日")

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

PROMPT_TEMPLATE = """
あなたはSEOに強い恋愛カウンセラーです。

【必須条件】
・主キーワード「{primary}」を自然に含める
・具体例多め、抽象論禁止
・600文字以上
・以下の構成を厳守

【構成】
タイトル：
要約：
結論：
相手の心理：
具体的な行動：（箇条書き）
避けたい行動：（箇条書き）
よくある勘違い：
まとめ：

【相談内容】
{question}
"""

# =========================
# Parse
# =========================

def extract_block(text, label):
    pattern = rf"{label}：([\s\S]*?)(?=\n\S+：|$)"
    m = re.search(pattern, text)
    return safe(m.group(1)) if m else ""

# =========================
# Main
# =========================

def main():
    print("=== daily_update START ===")

    if not QUESTION_FILE.exists():
        print("questions.json not found")
        return

    questions = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
    q = next((x for x in questions if x.get("status") == "pending"), None)

    if not q:
        print("No pending questions")
        return

    seo = q["seo"]
    slug = q["slug"]

    prompt = PROMPT_TEMPLATE.format(
        primary=seo["primary_keyword"],
        question=q["question"]
    )

    try:
        res = llm(prompt, max_tokens=1500)
        out = res["choices"][0]["text"]
    except Exception as e:
        print("LLM error:", e)
        return

    title = extract_block(out, "タイトル")
    lead = extract_block(out, "要約")
    conclusion = extract_block(out, "結論")
    psychology = extract_block(out, "相手の心理")
    action = extract_block(out, "具体的な行動")
    ng = extract_block(out, "避けたい行動")
    misunderstanding = extract_block(out, "よくある勘違い")
    summary = extract_block(out, "まとめ")

    if not title or not conclusion:
        print("Invalid LLM output")
        return

    today = now()
    filename = f"{today.strftime('%Y-%m-%d')}-{slug}.html"
    url = f"posts/{filename}"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    html = template \
        .replace("{{TITLE}}", title) \
        .replace("{{META_DESCRIPTION}}", lead[:120]) \
        .replace("{{DATE_ISO}}", iso(today)) \
        .replace("{{DATE_JP}}", jp(today)) \
        .replace("{{PAGE_URL}}", url) \
        .replace("{{CANONICAL}}", f'<link rel="canonical" href="{url}">') \
        .replace("{{LEAD}}", lead) \
        .replace("{{QUESTION}}", q["question"]) \
        .replace("{{SUMMARY_ANSWER}}", conclusion) \
        .replace("{{PSYCHOLOGY}}", psychology) \
        .replace("{{ACTION_LIST}}", "".join(f"<li>{x}</li>" for x in action.splitlines() if x)) \
        .replace("{{NG_LIST}}", "".join(f"<li>{x}</li>" for x in ng.splitlines() if x)) \
        .replace("{{MISUNDERSTANDING}}", misunderstanding) \
        .replace("{{CONCLUSION}}", summary) \
        .replace("{{FAQ}}", "") \
        .replace("{{RELATED}}", "") \
        .replace("{{PREV}}", "") \
        .replace("{{NEXT}}", "")

    (POST_DIR / filename).write_text(html, encoding="utf-8")

    # 更新
    q["status"] = "done"
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
