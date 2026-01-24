import json
import os
import sys
import hashlib
import re
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths
# =========================

MODEL_PATH = "models/model.gguf"
QUESTIONS_PATH = "data/questions.json"

MAX_RETRY = 8
MIN_TITLE_LEN = 22
MIN_BODY_LEN = 150
RECENT_GENRE_BLOCK = 3
SEMANTIC_CHECK_N = 5
MAX_RELATED = 3

# =========================
# Utils
# =========================

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

# =========================
# LLM
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
# Question Generate（SEO特化）
# =========================

def generate():
    prompt = """
あなたは検索エンジン経由で読まれる「実体験の恋愛相談」を1件だけ生成します。

【SEO要件】
・検索されやすい悩み＋状況＋感情を含むタイトル
・誰の・いつから・何が起きているかを明確に
・共感される感情の揺れを必ず含める

【禁止】
・抽象論
・教科書的表現
・よくあるテンプレ相談

【文字数】
・タイトル：22文字以上
・本文：150文字以上

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""
    r = llm(prompt, max_tokens=900)
    text = r["choices"][0]["text"].strip()

    if "タイトル：" not in text or "質問：" not in text:
        return None

    title = text.split("タイトル：")[1].split("質問：")[0].strip()
    body = text.split("質問：")[1].strip()

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    return title, body

# =========================
# Genre（SEOクラスタ固定）
# =========================

def extract_genre(title, body):
    prompt = f"""
以下の恋愛相談を、SEO的に最適なジャンル1語で分類してください。
必ず下記から選んでください。

【選択肢】
片思い / 復縁 / 倦怠期 / 価値観のズレ / 浮気 / 遠距離 / 別れたい / 依存 / 年の差 / 結婚

【相談】
タイトル：{title}
質問：{body}
"""
    r = llm(prompt, max_tokens=20)
    return r["choices"][0]["text"].strip()

# =========================
# Semantic Duplicate
# =========================

def semantic_duplicate_check(title, body, past, n):
    recent = past[-n:]
    if not recent:
        return True

    titles = "\n".join(f"- {q['title']}" for q in recent)

    prompt = f"""
以下の新規相談が、過去相談と意味的に重複しているか判定してください。

出力は OK または NG のみ。

--- 過去 ---
{titles}

--- 新規 ---
タイトル：{title}
質問：{body}
"""
    r = llm(prompt, max_tokens=10)
    return r["choices"][0]["text"].strip() == "OK"

# =========================
# Related Articles
# =========================

def build_related(questions, genre):
    same = [q for q in questions if q.get("genre") == genre]
    same = same[-MAX_RELATED:]
    return [
        {
            "id": q["id"],
            "title": q["title"],
            "url": q["url"]
        }
        for q in same
    ]

# =========================
# Main
# =========================

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
        related = build_related(questions, genre)

        questions.append({
            "id": uid(),
            "title": title,
            "slug": slug,
            "question": body,
            "genre": genre,
            "related": related,
            "created_at": now(),
            "content_hash": h,
            "url": f"posts/{slug}.html"
        })

        save_json(QUESTIONS_PATH, questions)
        print("✅ SEO向け新規質問生成成功")
        return

    print("❌ 新規質問生成に失敗")
    sys.exit(1)

if __name__ == "__main__":
    main()
