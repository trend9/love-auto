import json
import os
from datetime import datetime
import random

QUESTIONS_FILE = "data/questions.json"
USED_FILE = "data/used_questions.json"

# SEOテンプレ質問（100個でも増やせる）
SEO_TEMPLATES = [
    "大学生で将来が不安です。今やるべきことは何でしょうか？",
    "恋人との価値観の違いに悩んでいます。別れるべきですか？",
    "仕事が続きません。自分に向いている仕事はどう見つけますか？",
    "30代で結婚を焦っています。何を優先すべきですか？",
    "人間関係で疲れやすい性格は直せますか？",
    # ↓ここにどんどん足す（100個以上OK）
]

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    questions = load_json(QUESTIONS_FILE, [])
    used = set(load_json(USED_FILE, []))

    new_questions = []

    for q in SEO_TEMPLATES:
        if q in used:
            continue

        new_questions.append({
            "question": q,
            "created_at": datetime.now().isoformat(),
            "used": False
        })
        used.add(q)

        # 一度に追加する数（調整可）
        if len(new_questions) >= 20:
            break

    if not new_questions:
        print("⚠ テンプレ質問が尽きています")
        return

    questions.extend(new_questions)

    save_json(QUESTIONS_FILE, questions)
    save_json(USED_FILE, list(used))

    print(f"✅ {len(new_questions)} 件の質問を追加しました")

if __name__ == "__main__":
    main()
