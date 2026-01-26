#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import random
import hashlib
import re
from datetime import datetime
from pathlib import Path
import requests

# =========================
# Settings
# =========================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

USED_TOPICS_PATH = DATA_DIR / "used_topics.json"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

SEARCH_QUERY = 'site:detail.chiebukuro.yahoo.co.jp 恋愛相談'
FETCH_COUNT = 10          # 検索取得件数
GENERATE_LIMIT = 3        # 返却する質問数

# =========================
# Persona pools
# =========================

AGES = list(range(18, 39))

PERSONS = [
    ("私", "女性"),
    ("私", "男性"),
    ("僕", "男性"),
    ("俺", "男性"),
]

RELATIONS = [
    "会社の先輩",
    "会社の後輩",
    "職場の同僚",
    "学校の先輩",
    "学校の後輩",
    "同級生",
    "部活の先輩",
    "部活の後輩",
]

EMOTIONS = [
    "胸が苦しくなってしまいます",
    "不安でいっぱいになります",
    "気持ちが落ち着かなくなります",
    "嫉妬してしまう自分が嫌になります",
]

CLOSINGS = [
    "どのように距離を縮めればよいのでしょうか？",
    "どんなアプローチが適切なのか教えてください。",
    "この状況でどう行動すべきか悩んでいます。",
    "一歩踏み出すべきか迷っています。",
]

# =========================
# Utils
# =========================

def now():
    return datetime.now().isoformat()

def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())

def topic_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()

def load_used_topics() -> set:
    if not USED_TOPICS_PATH.exists():
        return set()
    try:
        return set(json.loads(USED_TOPICS_PATH.read_text(encoding="utf-8")))
    except Exception:
        return set()

def save_used_topics(topics: set):
    USED_TOPICS_PATH.write_text(
        json.dumps(list(topics), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# =========================
# Google Search
# =========================

def google_search():
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": SEARCH_QUERY,
        "num": FETCH_COUNT,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    items = data.get("items", [])
    results = []

    for item in items:
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()
        if title:
            results.append({"title": title, "snippet": snippet})

    return results

# =========================
# Rewrite logic（非LLM）
# =========================

def remake_question(theme: str) -> dict:
    person, gender = random.choice(PERSONS)
    age = random.choice(AGES)
    relation = random.choice(RELATIONS)
    emotion = random.choice(EMOTIONS)
    closing = random.choice(CLOSINGS)

    body = (
        f"{person}は{age}歳の{gender}です。"
        f"{relation}のことが好きで、長い間片思いをしています。"
        f"{theme}ことがあり、そのたびに{emotion}。"
        f"しかし、どう距離を縮めればいいのかわかりません。"
        f"{closing}"
    )

    slug = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", theme)[:50] or "love-question"

    return {
        "question": body,
        "slug": slug,
        "created_at": now(),
    }

# =========================
# Public API
# =========================

def fetch_questions() -> list[dict]:
    used_topics = load_used_topics()
    results = []

    search_results = google_search()

    random.shuffle(search_results)

    for item in search_results:
        if len(results) >= GENERATE_LIMIT:
            break

        base_theme = item["title"]
        h = topic_hash(base_theme)

        if h in used_topics:
            continue

        q = remake_question(base_theme)
        results.append(q)
        used_topics.add(h)

    save_used_topics(used_topics)

    return results
