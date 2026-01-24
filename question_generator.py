import json
import os
import re
import unicodedata
from datetime import datetime
from llama_cpp import Llama

# =========================
# 設定
# =========================
MODEL_PATH = "./models/model.gguf"
QUESTIONS_PATH = "data/questions.json"
USED_PATH = "data/used_questions.json"

GENERATE_COUNT = 5
MAX_CONTEXT = 2048

# =========================
# LLM 初期化
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    n_threads=os.cpu_count() or 4,
    n_gpu_layers=0,
    verbose=False
)

# =========================
# ユーティリティ
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# slug 生成（SEO用）
# =========================
def slugify(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def unique_slug(base, existing_slugs):
    slug = base
    i = 2
    while slug in existing_slugs:
        slug = f"{base}-{i}"
        i += 1
    return slug

# =========================
# SEO特化プロンプト
# =========================
def build_prompt(existing_titles):
    banned = "\n".join(existing_titles[:50])

    return f"""
あなたは「恋愛相談サイト」の編集者です。
日本人が実際に検索しそうな【恋愛の悩み】を生成してください。

条件：
- 日本語
- 実在の人が検索する文言
- 1タイトル＝1悩み
- 恋愛相談に限定
- 説明文や前置きは禁止
- 箇条書き禁止
- 数字・記号禁止

すでに使われたタイトル（これらは絶対に出さない）：
{banned}

出力形式（JSONのみ）：
[
  {{
    "title": "検索されやすい質問タイトル",
    "question": "その悩みを具体的に書いた相談文（2〜4文）"
  }}
]

必ず {GENERATE_COUNT} 個出力してください。
"""

# =========================
# 質問生成
# =========================
def generate_questions(existing_titles):
    prompt = build_prompt(existing_titles)

    result = llm(
        prompt,
        max_tokens=800,
        temperature=0.9,
        top_p=0.95,
        repeat_penalty=1.1,
        stop=["</s>"]
    )

    text = result["choices"][0]["text"].strip()

    try:
        json_start = text.index("[")
        json_end = text.rindex("]") + 1
        parsed = json.loads(text[json_start:json_end])
    except Exception:
        return []

    cleaned = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        if "title" not in item or "question" not in item:
            continue
        cleaned.append({
            "title": item["title"].strip(),
            "question": item["question"].strip()
        })

    return cleaned

# =========================
# メイン処理
# =========================
def main():
    questions = load_json(QUESTIONS_PATH)
    used = load_json(USED_PATH)

    existing_slugs = set()

    # 🔧 既存データを完全正規化（id / slug / url 保証）
    for i, q in enumerate(questions):
        if "id" not in q or not q["id"]:
            q["id"] = f"legacy_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if "slug" not in q or not q["slug"]:
            base = slugify(q.get("title", q["id"]))
            q["slug"] = unique_slug(base, existing_slugs)

        q["url"] = f"posts/{q['slug']}.html"
        existing_slugs.add(q["slug"])

    existing_titles = {q.get("title", "") for q in questions}
    used_titles = {q.get("title", "") for q in used}

    new_items = generate_questions(list(existing_titles | used_titles))

    if not new_items:
        print("⚠ 質問を生成できませんでした")
        return

    now = datetime.now()

    for item in new_items:
        base_slug = slugify(item["title"])
        slug = unique_slug(base_slug, existing_slugs)
        existing_slugs.add(slug)

        qid = now.strftime("%Y%m%d_%H%M%S_%f")

        full = {
            "id": qid,
            "title": item["title"],
            "slug": slug,
            "question": item["question"],
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"posts/{slug}.html"
        }

        questions.append(full)
        used.append({"title": item["title"]})

    save_json(QUESTIONS_PATH, questions)
    save_json(USED_PATH, used)

    print(f"✅ {len(new_items)} 件のSEO質問を追加しました")

if __name__ == "__main__":
    main()
