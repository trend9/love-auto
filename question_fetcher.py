#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import random
import json
import os
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# =====================
# 設定
# =====================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

QUESTION_PATH = DATA_DIR / "questions.json"
USED_THEME_PATH = DATA_DIR / "used_themes.json"

SEARCH_URL = "https://www.google.com/search"
QUERY = "site:detail.chiebukuro.yahoo.co.jp 恋愛 片思い"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_FETCH = 10        # 検索結果数（存在確認用）
GENERATE_NUM = 1      # cron前提：1回1件

# =====================
# テンプレ素材
# =====================

AGES = list(range(18, 36))

GENDERS = ["女性", "男性"]

PRONOUNS = {
    "女性": ["私"],
    "男性": ["僕", "俺"]
}

RELATIONSHIPS = [
    "会社の先輩",
    "会社の後輩",
    "同じ部署の同僚",
    "学校の先輩",
    "学校の後輩",
    "同級生",
    "部活の先輩",
    "部活の後輩"
]

EMOTIONS = [
    "胸が苦しくなってしまいます",
    "不安な気持ちになります",
    "嫉妬してしまいます",
    "気持ちが抑えられません"
]

PROBLEMS = [
    "距離を縮める方法がわかりません",
    "どう行動すればいいかわかりません",
    "勇気が出ずに何もできません",
    "関係を壊してしまいそうで怖いです"
]

# =====================
# ユーティリティ
# =====================

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default

def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def theme_hash(gender, relationship, problem):
    raw = f"{gender}|{relationship}|{problem}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# =====================
# Google検索（存在確認のみ）
# =====================

def fetch_search_links():
    try:
        res = requests.get(
            SEARCH_URL,
            headers=HEADERS,
            params={"q": QUERY, "num": MAX_FETCH},
            timeout=10
        )
    except Exception:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    links = []

    for a in soup.select("a"):
        href = a.get("href", "")
        if "detail.chiebukuro.yahoo.co.jp" in href:
            clean = href.split("&")[0].replace("/url?q=", "")
            links.append(clean)

    return list(set(links))

# =====================
# 質問生成（完全オリジナル）
# =====================

def generate_question(used_themes: set):
    gender = random.choice(GENDERS)
    age = random.choice(AGES)
    pronoun = random.choice(PRONOUNS[gender])
    relationship = random.choice(RELATIONSHIPS)
    emotion = random.choice(EMOTIONS)
    problem = random.choice(PROBLEMS)

    h = theme_hash(gender, relationship, problem)
    if h in used_themes:
        return None, None

    text = (
        f"{pronoun}は{age}歳の{gender}です。"
        f"{relationship}のことが好きで、ずっと片思いをしています。"
        f"他の異性と話しているのを見ると{emotion}。"
        f"しかし、{problem}。"
        f"どのようにアプローチをすれば良いのでしょうか？"
    )

    return {
        "id": h,
        "question": text,
        "persona": {
            "age": age,
            "gender": gender,
            "pronoun": pronoun,
            "relationship": relationship
        },
        "used": False,
        "created_at": datetime.now().isoformat()
    }, h

# =====================
# メイン処理
# =====================

def main():
    print("=== question_fetcher START ===")

    used_themes = set(load_json(USED_THEME_PATH, []))
    questions = load_json(QUESTION_PATH, [])

    # 検索は「世の中に相談が存在するか」の確認だけ
    links = fetch_search_links()
    if not links:
        print("No source links found. Exit safely.")
        return

    generated = 0

    for _ in range(20):
        if generated >= GENERATE_NUM:
            break

        q, h = generate_question(used_themes)
        if not q:
            continue

        questions.append(q)
        used_themes.add(h)
        generated += 1

    if generated == 0:
        print("No unique question generated.")
        return

    save_json(QUESTION_PATH, questions)
    save_json(USED_THEME_PATH, list(used_themes))

    print(f"Generated {generated} question(s).")
    print("=== question_fetcher END ===")

if __name__ == "__main__":
    main()
