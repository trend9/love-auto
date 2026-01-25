import re
import hashlib
from datetime import datetime
from llama_cpp import Llama

# =========================
# Settings
# =========================

MODEL_PATH = "./models/model.gguf"

GENERATE_COUNT = 5
MAX_RETRY = 30

MIN_TITLE_LEN = 20
MIN_BODY_LEN = 120

# =========================
# Utils
# =========================

def slugify_jp(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60]

def normalize(t):
    return "".join(t.split()).lower()

def content_hash(title, body):
    return hashlib.sha256(
        (normalize(title) + normalize(body)).encode("utf-8")
    ).hexdigest()

def now():
    return datetime.now().isoformat()

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
# Generate
# =========================

PROMPT = """
あなたは「実体験ベースの恋愛・人間関係相談」を1件生成してください。

【厳守】
・抽象論・テンプレ禁止
・期間・関係性・出来事を必ず含める
・感情の葛藤を明確に書く
・過去に見たことがある内容は禁止

【形式】
タイトル：20文字以上
質問：120文字以上
"""

def generate_one():
    r = llm(PROMPT, max_tokens=700)
    t = r["choices"][0]["text"].strip()

    if "タイトル：" not in t or "質問：" not in t:
        return None

    title = t.split("タイトル：")[1].split("質問：")[0].strip()
    body = t.split("質問：")[1].strip()

    if len(title) < MIN_TITLE_LEN or len(body) < MIN_BODY_LEN:
        return None

    return {
        "title": title,
        "question": body,
        "slug": slugify_jp(title),
        "created_at": now(),
        "content_hash": content_hash(title, body),
    }

def generate_questions():
    results = []
    hashes = set()

    for _ in range(MAX_RETRY):
        if len(results) >= GENERATE_COUNT:
            break

        q = generate_one()
        if not q:
            continue

        if q["content_hash"] in hashes:
            continue

        hashes.add(q["content_hash"])
        results.append(q)

    if len(results) < GENERATE_COUNT:
        raise RuntimeError("質問生成に失敗（必要数未達）")

    return results
