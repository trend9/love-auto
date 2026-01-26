#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import json
import hashlib
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

QUESTION_PATH = DATA_DIR / "questions.json"
USED_PATH = DATA_DIR / "used_questions.json"

AGES = list(range(18, 36))
GENDERS = ["女性", "男性"]
PRONOUNS = {
    "女性": "私",
    "男性": "僕"
}

RELATIONSHIPS = [
    "会社の先輩", "会社の後輩", "同僚",
    "学校の先輩", "学校の後輩", "同級生"
]

EMOTIONS = [
    "胸が苦しくなります",
    "不安になります",
    "嫉妬してしまいます"
]

PROBLEMS = [
    "距離の縮め方がわかりません",
    "どう行動すればいいかわかりません"
]

def load(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save(path, data):
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def make_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def main():
    print("=== question_fetcher START ===")

    questions = load(QUESTION_PATH, [])
    used_ids = set(load(USED_PATH, []))

    for _ in range(30):
        gender = random.choice(GENDERS)
        age = random.choice(AGES)
        relation = random.choice(RELATIONSHIPS)
        emotion = random.choice(EMOTIONS)
        problem = random.choice(PROBLEMS)

        question_text = (
            f"{PRONOUNS[gender]}は{age}歳の{gender}です。"
            f"{relation}に片思いしています。"
            f"{emotion}。{problem}。"
            "どうすればいいでしょうか？"
        )

        qid = make_id(question_text)

        if qid in used_ids:
            continue

        questions.append({
            "id": qid,
            "question": question_text,
            "used": False,
            "created_at": datetime.now().isoformat()
        })

        used_ids.add(qid)
        break

    save(QUESTION_PATH, questions)
    save(USED_PATH, list(used_ids))

    print("✔ question added")
    print("=== question_fetcher END ===")

if __name__ == "__main__":
    main()
