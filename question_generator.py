import json
import os
import sys
import hashlib
import re
from datetime import datetime
from llama_cpp import Llama

MODEL_PATH = "models/model.gguf"
QUESTIONS_PATH = "data/questions.json"

MAX_RETRY = 20
MIN_TITLE_LEN = 20
MIN_BODY_LEN = 120
RECENT_GENRE_BLOCK = 3     # 同ジャンル連続防止
SEMANTIC_CHECK_N = 10      # 意味被りチェック件数

# -------------------------
# Utils
# -------------------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def normalize(t):
    return "".join(t.split()).lower()

def content_hash(title, body):
    return hashlib.sha256((normalize(title) + normalize(body)).encode()).hexdigest()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def uid():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def slugify_jp(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60]

def recent_genres(questions, n):
    return [q.get("genre") for q in questions[-n:] if "genre" in q]

# -------------------------
# LLM
# -------------------------
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.15,
    verbose=False,
)

# -------------------------
# Step 1: 質問生成
# -------------------------
def generate():
    prompt = """
あなたは「恋愛・人間関係の実体験相談」を1件だけ生成してください。

【厳守】
・抽象論、テンプレ禁止
・具体的な期間／関係性／出来事を含める
・感情の葛藤を必ず入れる
・過去に見たことがある相談は禁止

【文字数】
・タイトル20文字以上
・本文120文字以上

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""
    r = llm(prompt, max_tokens=700)
    text = r["choices"][0]["text"].strip()

    if "タイトル：" not in text or "質問：" not in text:
        return None

    title = text.split("タイトル：")[1].split("質問：")[0].strip()
    body = text.split("質問：")[1].strip()

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    return title, body

# -------------------------
# Step 2: ジャンル抽出
# -------------------------
def extract_genre(title, body):
    prompt = f"""
以下の恋愛相談を、最も近いジャンル1語で分類してください。

【例】
片思い / 復縁 / 浮気 / 冷却期間 / 遠距離 / 年の差 / 職場恋愛 / 価値観のズレ

【ルール】
・必ず1語
・説明禁止

--- 相談 ---
タイトル：{title}
質問：{body}
"""
    r = llm(prompt, max_tokens=20)
    return r["choices"][0]["text"].strip()

# -------------------------
# Step 3: 意味的被りチェック
# -------------------------
def semantic_duplicate_check(title, body, past_questions, n):
    recent = past_questions[-n:]
    if not recent:
        return True

    summaries = "\n".join(f"- {q['title']}" for q in recent)

    prompt = f"""
以下の新しい恋愛相談が、過去の相談と
「意味的にほぼ同じ内容」かどうかを判定してください。

【基準】
・状況や悩みの構造が似ていれば NG
・表現違いでも中身が同じなら NG
・明確に違えば OK

【出力】
OK または NG のみ

--- 過去の相談 ---
{summaries}

--- 新しい相談 ---
タイトル：{title}
質問：{body}
"""
    r = llm(prompt, max_tokens=10)
    return r["choices"][0]["text"].strip() == "OK"

# -------------------------
# Main
# -------------------------
def main():
    questions = load_json(QUESTIONS_PATH, [])
    hashes = {q["content_hash"] for q in questions if "content_hash" in q}

    for _ in range(MAX_RETRY):
        result = generate()
        if not result:
            continue

        title, body = result
        h = content_hash(title, body)
        if h in hashes:
            continue

        genre = extract_genre(title, body)

        if genre in recent_genres(questions, RECENT_GENRE_BLOCK):
            continue

        if not semantic_duplicate_check(title, body, questions, SEMANTIC_CHECK_N):
            continue

        slug = slugify_jp(title)

        new_q = {
            "id": uid(),
            "title": title,
            "slug": slug,
            "question": body,
            "genre": genre,
            "created_at": now(),
            "content_hash": h,
            "url": f"posts/{slug}.html"
        }

        questions.append(new_q)
        save_json(QUESTIONS_PATH, questions)
        print("✅ 新規質問生成成功")
        return

    print("❌ 新規質問生成に失敗（致命的）")
    sys.exit(1)

if __name__ == "__main__":
    main()
