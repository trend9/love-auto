#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
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
    "女性": ["私"],
    "男性": ["僕", "俺"]
}

RELATIONSHIPS = [
    "会社の先輩",
    "会社の後輩",
    "同僚",
    "学校の先輩",
    "学校の後輩",
    "同級生"
]

EMOTIONS = [
    "胸が苦しくなります",
    "不安になります",
    "嫉妬してしまいます"
]

PROBLEMS = [
    "距離の縮め方がわかりません",
    "どう行動すればいいかわかりません",
    "脈ありか判断できません"
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

def make_slug(relationship, problem):
    return (
        relationship
        .replace("会社の", "company-")
        .replace("学校の", "school-")
        .replace("同級生", "classmate")
        .replace("先輩", "senpai")
        .replace("後輩", "kouhai")
        + "-"
        + problem
        .replace("距離の縮め方がわかりません", "how-to-close-distance")
        .replace("どう行動すればいいかわかりません", "what-should-i-do")
        .replace("脈ありか判断できません", "signs-of-interest")
    )

def make_hash(slug):
    return hashlib.sha256(slug.encode("utf-8")).hexdigest()

def main():
    print("=== question_fetcher START ===")

    questions = load(QUESTION_PATH, [])
    used = set(load(USED_PATH, []))

    generated = 0

    for _ in range(50):
        gender = random.choice(GENDERS)
        age = random.choice(AGES)
        relationship = random.choice(RELATIONSHIPS)
        problem = random.choice(PROBLEMS)
        emotion = random.choice(EMOTIONS)

        slug = make_slug(relationship, problem)
        qid = make_hash(slug)

        if qid in used:
            continue

        question_text = (
            f"{PRONOUNS[gender][0]}は{age}歳の{gender}です。"
            f"{relationship}に片思いしています。"
            f"{emotion}。{problem}。"
            "どうすればいいでしょうか？"
        )

        questions.append({
            "id": qid,
            "slug": slug,
            "question": question_text,
            "seo": {
                "primary_keyword": f"{relationship} 片思い",
                "secondary_keywords": [
                    "距離 縮め方",
                    "脈あり サイン",
                    "恋愛 悩み"
                ]
            },
            "persona": {
                "age": age,
                "gender": gender,
                "relationship": relationship
            },
            "status": "pending",
            "created_at": datetime.now().isoformat()
        })

        used.add(qid)
        generated += 1

        if generated >= 5:
            break

    save(QUESTION_PATH, questions)
    save(USED_PATH, list(used))

    print(f"Generated {generated} questions")
    print("=== question_fetcher END ===")

if __name__ == "__main__":
    main()
