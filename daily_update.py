import os
import json
import re
import hashlib
from datetime import datetime
from difflib import SequenceMatcher
from llama_cpp import Llama

# =========================
# Config
# =========================

MODEL_PATH = "./models/model.gguf"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
DATA_DIR = "data"
QUESTIONS_PATH = f"{DATA_DIR}/questions.json"
USED_QUESTIONS_PATH = f"{DATA_DIR}/used_questions.json"
SITE_URL = "https://trend9.github.io/love-auto"

MAX_RETRY = 8
MAX_CONTEXT = 4096

MIN_SIMILARITY = 0.82  # 意味的に似すぎたらNG

# =========================
# LLM
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1,
    verbose=False,
)

# =========================
# Utils
# =========================

EN_WORD_RE = re.compile(r"\b[a-zA-Z]{3,}\b")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def today():
    now = datetime.now()
    return {
        "iso": now.isoformat(),
        "jp": now.strftime("%Y年%m月%d日")
    }

def uid():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

def slugify_jp(text):
    return re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)[:60]

def normalize(text):
    return re.sub(r"\s+", "", text)

def content_hash(title, body):
    return hashlib.sha256((normalize(title) + normalize(body)).encode()).hexdigest()

def has_english_strict(text):
    return len(EN_WORD_RE.findall(text)) >= 2

def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# =========================
# Validation
# =========================

def is_duplicate_question(title, body, used):
    for q in used:
        if similarity(title, q["title"]) >= MIN_SIMILARITY:
            return True
        if similarity(body, q["question"]) >= MIN_SIMILARITY:
            return True
    return False

def validate_article_json(data):
    required_keys = [
        "lead", "summary", "psychology",
        "actions", "ng", "misunderstanding", "conclusion"
    ]

    for k in required_keys:
        if k not in data:
            return False

    if not isinstance(data["actions"], list) or len(data["actions"]) < 3:
        return False

    if not isinstance(data["ng"], list) or len(data["ng"]) < 2:
        return False

    text_blob = json.dumps(data, ensure_ascii=False)
    if has_english_strict(text_blob):
        return False

    return True

# =========================
# Question Generation
# =========================

def generate_question(used_questions):
    prompt = """
日本語のみで、実体験ベースの恋愛相談を1件生成してください。

【絶対条件】
・具体的な出来事（時期・状況・相手の行動）
・相談者の感情が明確
・抽象論・一般論は禁止
・タイトル20文字以上
・本文120文字以上

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""

    last_reason = ""

    for _ in range(MAX_RETRY):
        r = llm(prompt, max_tokens=600)
        text = r["choices"][0]["text"].strip()

        if "タイトル：" not in text or "質問：" not in text:
            last_reason = "形式不正"
            continue

        title = text.split("タイトル：")[1].split("質問：")[0].strip()
        body = text.split("質問：")[1].strip()

        if len(title) < 20 or len(body) < 120:
            last_reason = "文字数不足"
            continue

        if has_english_strict(text):
            last_reason = "英語混入"
            continue

        if is_duplicate_question(title, body, used_questions):
            last_reason = "意味重複"
            continue

        return title, body

    raise RuntimeError(f"質問生成失敗（理由: {last_reason}）")

# =========================
# Article Generation (JSON)
# =========================

def generate_article(question):
    prompt = f"""
以下のJSONのみを厳密に出力してください。
説明文・前置きは禁止。
英語は禁止。

{{
  "lead": "80文字以上",
  "summary": "120文字以上",
  "psychology": "150文字以上",
  "actions": ["行動1", "行動2", "行動3"],
  "ng": ["NG1", "NG2"],
  "misunderstanding": "100文字以上",
  "conclusion": "120文字以上"
}}

相談内容：
{question}
"""

    for _ in range(MAX_RETRY):
        r = llm(prompt, max_tokens=2200)
        raw = r["choices"][0]["text"].strip()

        try:
            data = json.loads(raw)
        except:
            continue

        if validate_article_json(data):
            return data

    raise RuntimeError("記事生成失敗")

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])
    used_questions = load_json(USED_QUESTIONS_PATH, [])

    title, body = generate_question(used_questions)
    slug = slugify_jp(title)
    h = content_hash(title, body)

    record = {
        "id": uid(),
        "title": title,
        "slug": slug,
        "question": body,
        "hash": h,
        "created_at": today()["iso"],
        "url": f"posts/{slug}.html"
    }

    questions.append(record)
    used_questions.append(record)

    save_json(QUESTIONS_PATH, questions)
    save_json(USED_QUESTIONS_PATH, used_questions)

    article = generate_article(body)

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    t = today()

    html = (
        tpl.replace("{{TITLE}}", title)
           .replace("{{META_DESCRIPTION}}", body[:120])
           .replace("{{DATE_ISO}}", t["iso"])
           .replace("{{DATE_JP}}", t["jp"])
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{slug}.html")
           .replace("{{LEAD}}", article["lead"])
           .replace("{{QUESTION}}", body)
           .replace("{{SUMMARY_ANSWER}}", article["summary"])
           .replace("{{PSYCHOLOGY}}", article["psychology"])
           .replace("{{ACTION_LIST}}", "".join(f"<li>{a}</li>" for a in article["actions"]))
           .replace("{{NG_LIST}}", "".join(f"<li>{n}</li>" for n in article["ng"]))
           .replace("{{MISUNDERSTANDING}}", article["misunderstanding"])
           .replace("{{CONCLUSION}}", article["conclusion"])
    )

    save_text(os.path.join(POST_DIR, f"{slug}.html"), html)

    print("✅ 完走：英語ゼロ・量産防止・Actions安定")

if __name__ == "__main__":
    main()
