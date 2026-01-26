import json
import os
import random
import sys

DATA_DIR = "data"
QUESTIONS_PATH = os.path.join(DATA_DIR, "questions.json")
USED_PATH = os.path.join(DATA_DIR, "used_questions.json")

# 安全なロード
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else default
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    used = set(load_json(USED_PATH, []))
    questions = load_json(QUESTIONS_PATH, [])

    # 疑似取得（スクレイピングの代替）
    candidate_questions = [
        "彼氏が急に冷たくなった理由がわからない",
        "好きだけど別れた方がいいのか迷っている",
        "既読無視が続くのは脈なし？",
        "元カノを忘れられない心理とは",
        "片思いが辛いときの気持ちの整理方法"
    ]

    random.shuffle(candidate_questions)

    for q in candidate_questions:
        if q not in used and q not in questions:
            questions.append(q)
            save_json(QUESTIONS_PATH, questions)
            print(f"✅ 質問を1件追加: {q}")
            return

    print("⚠️ 新規質問なし（全て使用済み）")

if __name__ == "__main__":
    main()
