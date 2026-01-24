import json
import os
import sys
import hashlib
from datetime import datetime
from llama_cpp import Llama

# ===============================
# 設定
# ===============================
MODEL_PATH = "models/model.gguf"
QUESTIONS_PATH = "data/questions.json"
MAX_RETRY = 7

# ===============================
# ユーティリティ
# ===============================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_text(text: str) -> str:
    return "".join(text.split()).lower()

def content_hash(title: str, question: str) -> str:
    base = normalize_text(title) + normalize_text(question)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def uid():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

# ===============================
# LLM 初期化
# ===============================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.15,
    verbose=False,
)

# ===============================
# 質問生成（薄くならない）
# ===============================
def generate_question():
    prompt = """
あなたは「恋愛・人間関係の実体験相談」を生成する専門家です。

【絶対ルール】
- 抽象論・一般論・テンプレ禁止
- 具体的な状況（関係性／期間／出来事）を必ず含める
- 感情の揺れ・葛藤・迷いを必ず1つ以上含める
- 1問のみ生成
- 過去に見たことがあるような質問は禁止

【文字量】
- タイトル：20文字以上
- 質問本文：120文字以上

【出力形式（厳守）】
タイトル：〇〇〇〇
質問：〇〇〇〇
"""

    result = llm(
        prompt,
        max_tokens=700,
        stop=["\n\n"],
    )

    text = result["choices"][0]["text"].strip()

    if "タイトル：" not in text or "質問：" not in text:
        return None

    try:
        title = text.split("タイトル：")[1].split("質問：")[0].strip()
        question = text.split("質問：")[1].strip()
        if len(title) < 20 or len(question) < 120:
            return None
        return title, question
    except Exception:
        return None

# ===============================
# メイン処理（失敗不可）
# ===============================
def main():
    questions = load_json(QUESTIONS_PATH, [])
    existing_hashes = {
        q.get("content_hash") for q in questions if "content_hash" in q
    }

    for _ in range(MAX_RETRY):
        generated = generate_question()
        if not generated:
            continue

        title, question = generated
        h = content_hash(title, question)

        if h in existing_hashes:
            continue

        qid = uid()
        slug = title.replace(" ", "").replace("　", "")
        slug = slug.replace("/", "").replace("?", "").replace("？", "")
        slug = f"{slug}-{qid[-6:]}"

        new_q = {
            "id": qid,
            "title": f"{title}_{qid[-6:]}",
            "slug": slug,
            "question": question,
            "created_at": now(),
            "content_hash": h,
            "url": f"posts/{slug}.html",
        }

        questions.append(new_q)
        save_json(QUESTIONS_PATH, questions)
        print("✅ 新しい質問を生成しました")
        return

    print("❌ 質問生成に失敗しました（重複・条件未達）")
    sys.exit(1)

if __name__ == "__main__":
    main()
