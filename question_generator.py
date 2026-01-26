#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import hashlib
import random
from datetime import datetime
from pathlib import Path
from llama_cpp import Llama

# =========================
# Settings
# =========================

BASE_DIR = Path(__file__).parent

MODEL_PATH = BASE_DIR / "models" / "model.gguf"

# cron前提：多く作らない
GENERATE_COUNT = 3
MAX_RETRY = 20

MIN_TITLE_LEN = 20
MIN_BODY_LEN = 120

# =========================
# Utils
# =========================

def slugify_jp(text: str) -> str:
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60] or "love-question"

def normalize(t: str) -> str:
    return "".join(t.split()).lower()

def content_hash(title: str, body: str) -> str:
    return hashlib.sha256(
        (normalize(title) + normalize(body)).encode("utf-8")
    ).hexdigest()

def now() -> str:
    return datetime.now().isoformat()

# =========================
# LLM
# =========================

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
あなたは「実体験ベースの恋愛・人間関係の悩み相談」を1件生成してください。

【厳守】
・テンプレ・抽象論は禁止
・期間、関係性、具体的な出来事を必ず含める
・感情の揺れや迷いをはっきり書く
・ネットでよく見る定番相談は禁止

【形式】
タイトル：20文字以上
質問：120文字以上
""".strip()

# =========================
# Generate core
# =========================

def generate_one() -> dict | None:
    r = llm(PROMPT, max_tokens=700)
    text = r["choices"][0]["text"].strip()

    if "タイトル：" not in text or "質問：" not in text:
        return None

    try:
        title = text.split("タイトル：", 1)[1].split("質問：", 1)[0].strip()
        body = text.split("質問：", 1)[1].strip()
    except Exception:
        return None

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    slug = slugify_jp(title)

    return {
        "title": title,
        "question": body,
        "slug": slug,
        "created_at": now(),
        "content_hash": content_hash(title, body),
    }

# =========================
# Public API
# =========================

def generate_questions() -> list[dict]:
    results = []
    hashes = set()

    for _ in range(MAX_RETRY):
        if len(results) >= GENERATE_COUNT:
            break

        q = generate_one()
        if not q:
            continue

        if q["content_hash"] in hashes:
            continue

        hashes.add(q["content_hash"])
        results.append(q)

    # cron前提：0件でも落とさない
    if not results:
        return []

    # 毎回順序を固定しない
    random.shuffle(results)

    return results
