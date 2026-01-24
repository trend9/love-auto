import json
import os
import re
import hashlib
import sys
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths
# =========================

MODEL_PATH = "./models/model.gguf"
QUESTIONS_PATH = "data/questions.json"

MAX_RETRY = 15
MIN_TITLE_LEN = 20
MIN_BODY_LEN = 120

# =========================
# Utils
# =========================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def uid():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def now():
    return datetime.now().isoformat()

def slugify_jp(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60]

def normalize(t):
    return "".join(t.split()).lower()

def content_hash(title, body):
    return hashlib.sha256((normalize(title)+normalize(body)).encode()).hexdigest()

# =========================
# LLM（質問生成専用）
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.15,
    verbose=False,
)

# =========================
# Generate
# =========================

def generate_question():
    prompt = """
あなたは「実体験ベースの恋愛・人間関係相談」を1件生成してください。

【厳守】
・抽象論・テンプレ禁止
・期間・関係性・出来事を含める
・感情の葛藤を明確に書く
・過去に見たことがある内容は禁止

【形式】
タイトル：20文字以上
質問：120文字以上
"""
    r = llm(prompt, max_tokens=700)
    t = r["choices"][0]["text"].strip()

    if "タイトル：" not in t or "質問：" not in t:
        return None

    title = t.split("タイトル：")[1].split("質問：")[0].strip()
    body = t.split("質問：")[1].strip()

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    return title, body

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])
    hashes = {q["content_hash"] for q in questions}

    for _ in range(MAX_RETRY):
        q = generate_question()
        if not q:
            continue

        title, body = q
        h = content_hash(title, body)
        if h in hashes:
            continue

        slug = slugify_jp(title)

        questions.append({
            "id": uid(),
            "title": title,
            "slug": slug,
            "question": body,
            "created_at": now(),
            "content_hash": h,
            "url": f"posts/{slug}.html"
        })

        save_json(QUESTIONS_PATH, questions)
        print("✅ 新規質問生成成功")
        return

    print("❌ 質問生成に失敗（致命的）")
    sys.exit(1)

if __name__ == "__main__":
    main()
