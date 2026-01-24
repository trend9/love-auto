import json
import os
import re
import unicodedata
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths / Settings
# =========================
MODEL_PATH = "./models/model.gguf"
QUESTIONS_PATH = "data/questions.json"
USED_PATH = "data/used_questions.json"

GENERATE_COUNT = 5
MAX_CONTEXT = 2048

# =========================
# LLM Init（失敗しても後続で必ず救済）
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    n_threads=os.cpu_count() or 4,
    n_gpu_layers=0,
    verbose=False
)

# =========================
# JSON Utils（壊れても止まらない）
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# Slug Utils
# =========================
def slugify(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def unique_slug(base, existing):
    slug = base
    i = 2
    while slug in existing:
        slug = f"{base}-{i}"
        i += 1
    return slug

# =========================
# Prompt
# =========================
def build_prompt(existing_titles):
    banned = "\n".join(list(existing_titles)[:50])
    return f"""
日本人が検索しそうな恋愛の悩みを作ってください。

条件：
- 日本語
- 恋愛相談のみ
- 説明文・箇条書き禁止
- JSONのみ出力

禁止タイトル：
{banned}

出力形式：
[
  {{
    "title": "質問タイトル",
    "question": "相談文"
  }}
]

{GENERATE_COUNT}件必ず出力。
"""

# =========================
# 最終保険（絶対に1件返す）
# =========================
def safe_fallback_questions():
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return [
        {
            "title": f"恋人の気持ちが分からなくなったときの向き合い方_{now}",
            "question": "最近、恋人の態度が以前と違うように感じて不安です。どのように気持ちを整理し、話し合えばいいでしょうか。"
        }
    ]

# =========================
# Question Generation（失敗不可）
# =========================
def generate_questions(existing_titles):
    try:
        result = llm(
            build_prompt(existing_titles),
            max_tokens=800,
            temperature=0.9
        )

        text = result["choices"][0]["text"]

        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end <= start:
            return safe_fallback_questions()

        parsed = json.loads(text[start:end])

        valid = []
        for q in parsed:
            if (
                isinstance(q, dict)
                and isinstance(q.get("title"), str)
                and isinstance(q.get("question"), str)
                and q["title"].strip()
                and q["question"].strip()
            ):
                valid.append(q)

        if valid:
            return valid

        return safe_fallback_questions()

    except Exception:
        return safe_fallback_questions()

# =========================
# Main（ここで0件は絶対に起きない）
# =========================
def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("posts", exist_ok=True)

    questions = load_json(QUESTIONS_PATH)
    used = load_json(USED_PATH)

    if not isinstance(used, list):
        used = []

    existing_slugs = set()
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            continue

        if "id" not in q or not q["id"]:
            q["id"] = f"legacy_{i}"

        if "title" not in q or not q["title"]:
            q["title"] = f"既存質問_{i}"

        if "slug" not in q or not q["slug"]:
            q["slug"] = slugify(q["title"]) or q["id"]

        q["url"] = f"posts/{q['slug']}.html"
        existing_slugs.add(q["slug"])

    existing_titles = {q["title"] for q in questions if isinstance(q, dict)}

    new_items = generate_questions(existing_titles)

    # 念のための最終保険
    if not new_items:
        new_items = safe_fallback_questions()

    now = datetime.now()

    for item in new_items:
        base = slugify(item["title"]) or now.strftime("%Y%m%d%H%M%S")
        slug = unique_slug(base, existing_slugs)
        existing_slugs.add(slug)

        questions.append({
            "id": now.strftime("%Y%m%d_%H%M%S_%f"),
            "title": item["title"],
            "slug": slug,
            "question": item["question"],
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"posts/{slug}.html"
        })

        used.append({"title": item["title"]})

    # 最終保証：questions.json が空なら強制1件
    if not questions:
        fallback = safe_fallback_questions()[0]
        slug = slugify(fallback["title"])
        questions.append({
            "id": "force_1",
            "title": fallback["title"],
            "slug": slug,
            "question": fallback["question"],
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "url": f"posts/{slug}.html"
        })

    save_json(QUESTIONS_PATH, questions)
    save_json(USED_PATH, used)

if __name__ == "__main__":
    main()
