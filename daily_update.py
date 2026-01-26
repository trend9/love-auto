#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from llama_cpp import Llama

from question_fetcher import fetch_questions

# =========================
# Paths / Settings
# =========================

BASE_DIR = Path(__file__).parent

MODEL_PATH = BASE_DIR / "models" / "model.gguf"
DATA_DIR = BASE_DIR / "data"
ARTICLE_DIR = DATA_DIR / "articles"

ARTICLE_DIR.mkdir(parents=True, exist_ok=True)

# cron前提：必ず1本
DAILY_GENERATE_COUNT = 1

MIN_TITLE_LEN = 20
MIN_BODY_LEN = 600

# =========================
# Utils
# =========================

def now():
    return datetime.now().isoformat()

def normalize(t: str) -> str:
    return "".join(t.split()).lower()

def content_hash(title: str, body: str) -> str:
    return hashlib.sha256(
        (normalize(title) + normalize(body)).encode("utf-8")
    ).hexdigest()

def slugify_jp(text: str) -> str:
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60] or "love-article"

# =========================
# LLM
# =========================

print("Initializing LLM...")

llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=2048,
    temperature=0.85,
    top_p=0.95,
    repeat_penalty=1.1,
    verbose=False,
)

# =========================
# Prompt
# =========================

def build_prompt(question: str) -> str:
    return f"""
以下は、実際の恋愛相談です。
相談者の立場・年齢・人称を尊重しながら、
読み物として成立する「本気の回答記事」を書いてください。

【重要ルール】
・説教・精神論・一般論は禁止
・相談者の感情に寄り添う
・「あなたの場合は〜」と個別化する
・600文字以上
・人称は本文内で自然に言及する
・出力は必ず下記形式のみ

【出力形式】
タイトル：
本文：

【相談内容】
{question}
""".strip()

# =========================
# Parse
# =========================

def parse_article(text: str) -> dict | None:
    if "タイトル：" not in text or "本文：" not in text:
        return None

    try:
        title = text.split("タイトル：", 1)[1].split("本文：", 1)[0].strip()
        body = text.split("本文：", 1)[1].strip()
    except Exception:
        return None

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    return {
        "title": title,
        "body": body,
        "slug": slugify_jp(title),
        "created_at": now(),
        "content_hash": content_hash(title, body),
    }

# =========================
# Core
# =========================

def generate_article(question: str) -> dict | None:
    prompt = build_prompt(question)

    try:
        r = llm(prompt, max_tokens=1300)
        text = r["choices"][0]["text"].strip()
    except Exception:
        return None

    return parse_article(text)

def save_article(article: dict):
    path = ARTICLE_DIR / f"{article['slug']}.json"
    path.write_text(
        json.dumps(article, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# =========================
# Main
# =========================

def main():
    print("=== daily_update START ===")

    questions = fetch_questions()
    if not questions:
        print("No questions. Exit normally.")
        return

    generated = 0

    for q in questions:
        if generated >= DAILY_GENERATE_COUNT:
            break

        question_text = q["question"]
        print("[GEN]", question_text[:40])

        article = generate_article(question_text)
        if not article:
            print("✖ Generation failed")
            continue

        save_article(article)
        generated += 1
        print("✔ Saved:", article["slug"])

    print(f"=== daily_update END ({generated} article) ===")

# =========================
# Entrypoint
# =========================

if __name__ == "__main__":
    main()
