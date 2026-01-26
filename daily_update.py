#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import random
import hashlib
from pathlib import Path
from datetime import datetime
from llama_cpp import Llama

# =========================
# Settings
# =========================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ARTICLE_DIR = DATA_DIR / "articles"
QUESTION_FILE = DATA_DIR / "questions.json"

MODEL_PATH = BASE_DIR / "models" / "model.gguf"

ARTICLE_DIR.mkdir(parents=True, exist_ok=True)

DAILY_GENERATE_COUNT = 1
MAX_RETRY = 15

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
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.15,
    verbose=False,
)

# =========================
# Prompt
# =========================

PROMPT = """
以下の恋愛相談に対して、
第三者として現実的で具体的なアドバイスをしてください。

【条件】
・抽象論は禁止
・行動ベースで説明
・600文字以上
・相談者の年齢・立場を意識する

【形式】
タイトル：
本文：
""".strip()

# =========================
# Parse
# =========================

def parse_article(text: str):
    if "タイトル：" not in text or "本文：" not in text:
        return None

    title = text.split("タイトル：", 1)[1].split("本文：", 1)[0].strip()
    body = text.split("本文：", 1)[1].strip()

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

def load_questions():
    if not QUESTION_FILE.exists():
        return []

    return json.loads(QUESTION_FILE.read_text(encoding="utf-8"))

def save_questions(data):
    QUESTION_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def save_article(article):
    path = ARTICLE_DIR / f"{article['slug']}.json"
    path.write_text(
        json.dumps(article, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def generate_one(prompt):
    r = llm(prompt, max_tokens=1200)
    text = r["choices"][0]["text"].strip()
    return parse_article(text)

# =========================
# Main
# =========================

def main():
    print("=== daily_update START ===")

    questions = load_questions()
    targets = [q for q in questions if not q.get("used")]

    if not targets:
        print("No unused questions. Exit.")
        return

    q = targets[0]

    prompt = (
        PROMPT
        + "\n\n相談者情報：\n"
        + f"{q['persona']['age']}歳 / {q['persona']['gender']} / {q['persona']['relationship']}\n\n"
        + "相談内容：\n"
        + q["question"]
    )

    for _ in range(MAX_RETRY):
        article = generate_one(prompt)
        if not article:
            continue

        save_article(article)
        q["used"] = True
        q["used_at"] = now()
        save_questions(questions)

        print("✔ Article generated:", article["slug"])
        break

    print("=== daily_update END ===")

if __name__ == "__main__":
    main()
