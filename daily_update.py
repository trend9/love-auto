import os
import json
import re
import hashlib
from datetime import datetime
from llama_cpp import Llama

# =========================
# Config
# =========================

MODEL_PATH = "./models/model.gguf"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
QUESTIONS_PATH = "data/questions.json"
SITE_URL = "https://trend9.github.io/love-auto"

MAX_RETRY = 8
MAX_CONTEXT = 4096

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

def esc(t):
    return (
        t.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )

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

def normalize(t):
    return "".join(t.split()).lower()

def content_hash(title, body):
    return hashlib.sha256((normalize(title) + normalize(body)).encode()).hexdigest()

def ascii_ratio(text):
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return ascii_count / max(len(text), 1)

def has_english_strict(text):
    return ascii_ratio(text) > 0.02

# =========================
# Question Generation
# =========================

def generate_question():
    prompt = """
日本語のみで、実体験ベースの恋愛相談を1件生成してください。

【条件】
・具体的な出来事と感情
・タイトル20文字以上
・本文120文字以上

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""

    for _ in range(MAX_RETRY):
        r = llm(prompt, max_tokens=600)
        text = r["choices"][0]["text"].strip()

        if "タイトル：" not in text or "質問：" not in text:
            continue

        title = text.split("タイトル：")[1].split("質問：")[0].strip()
        body = text.split("質問：")[1].strip()

        if len(title) < 20 or len(body) < 120:
            continue

        if has_english_strict(text):
            continue

        return title, body

    raise RuntimeError("質問生成失敗")

# =========================
# Article Generation (JSON)
# =========================

def generate_article(question):
    prompt = f"""
以下のJSONのみを出力してください。
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

        if has_english_strict(json.dumps(data, ensure_ascii=False)):
            continue

        return data

    raise RuntimeError("記事生成失敗")

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])

    title, body = generate_question()
    slug = slugify_jp(title)

    questions.append({
        "id": uid(),
        "title": title,
        "slug": slug,
        "question": body,
        "created_at": today()["iso"],
        "content_hash": content_hash(title, body),
        "url": f"posts/{slug}.html"
    })

    save_json(QUESTIONS_PATH, questions)

    article = generate_article(body)

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    t = today()

    html = (
        tpl.replace("{{TITLE}}", esc(title))
           .replace("{{META_DESCRIPTION}}", esc(body[:120]))
           .replace("{{DATE_ISO}}", t["iso"])
           .replace("{{DATE_JP}}", t["jp"])
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{slug}.html")
           .replace("{{LEAD}}", esc(article["lead"]))
           .replace("{{QUESTION}}", esc(body))
           .replace("{{SUMMARY_ANSWER}}", esc(article["summary"]))
           .replace("{{PSYCHOLOGY}}", esc(article["psychology"]))
           .replace("{{ACTION_LIST}}", "\n".join(f"<li>{esc(a)}</li>" for a in article["actions"]))
           .replace("{{NG_LIST}}", "\n".join(f"<li>{esc(n)}</li>" for n in article["ng"]))
           .replace("{{MISUNDERSTANDING}}", esc(article["misunderstanding"]))
           .replace("{{CONCLUSION}}", esc(article["conclusion"]))
           .replace("{{RELATED}}", "")
           .replace("{{PREV}}", "")
           .replace("{{NEXT}}", "")
           .replace("{{CANONICAL}}", "")
           .replace("{{FAQ}}", "")
    )

    save_text(os.path.join(POST_DIR, f"{slug}.html"), html)
    print("✅ 完走：Actions安定・量産防止OK")

if __name__ == "__main__":
    main()
