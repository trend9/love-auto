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

MODEL_PATH = BASE_DIR / "models" / "model.gguf"
DATA_DIR = BASE_DIR / "data"
ARTICLE_DIR = DATA_DIR / "articles"

ARTICLE_DIR.mkdir(parents=True, exist_ok=True)

DAILY_GENERATE_COUNT = 1   # ← 安定性最優先
MAX_RETRY = 20

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
以下の「恋愛・人間関係の悩み相談」に対して、
経験豊富な第三者として真剣に回答してください。

【条件】
・抽象論・精神論は禁止
・具体的な行動・考え方を示す
・600文字以上
・読み物として成立させる

【形式】
タイトル：
本文：
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

def generate_one(prompt: str) -> dict | None:
    try:
        r = llm(prompt, max_tokens=1200)
        text = r["choices"][0]["text"].strip()
    except Exception:
        return None

    return parse_article(text)

def load_questions() -> list[str]:
    q_file = DATA_DIR / "questions.json"
    if not q_file.exists():
        return []

    try:
        return json.loads(q_file.read_text(encoding="utf-8"))
    except Exception:
        return []

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

    questions = load_questions()
    if not questions:
        print("No questions. Exit normally.")
        return

    random.shuffle(questions)

    generated = 0
    used_hashes = set()

    for q in questions:
        if generated >= DAILY_GENERATE_COUNT:
            break

        prompt = PROMPT + "\n\n相談内容：\n" + q
        print("[GEN]", q[:40])

        for _ in range(MAX_RETRY):
            article = generate_one(prompt)
            if not article:
                continue

            if article["content_hash"] in used_hashes:
                continue

            save_article(article)
            used_hashes.add(article["content_hash"])
            generated += 1
            print("✔ Saved:", article["slug"])
            break

    print(f"=== daily_update END ({generated} articles) ===")

if __name__ == "__main__":
    main()
