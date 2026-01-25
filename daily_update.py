import os
import json
import re
import hashlib
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths / Config
# =========================

MODEL_PATH = "./models/model.gguf"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
QUESTIONS_PATH = "data/questions.json"
SITE_URL = "https://trend9.github.io/love-auto"

MAX_CONTEXT = 4096
MAX_Q_RETRY = 5
MAX_ARTICLE_RETRY = 4
MAX_CLEAN_RETRY = 2

ASCII_RATIO_LIMIT = 0.03

# =========================
# LLM（単一ロード）
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    temperature=0.6,          # 清書向けに低め
    top_p=0.9,
    repeat_penalty=1.05,
    verbose=False,
)

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
    text = re.sub(r"[^\wぁ-んァ-ン一-龥]", "", text)
    return text[:60]

def normalize(t):
    return "".join(t.split()).lower()

def content_hash(title, body):
    return hashlib.sha256((normalize(title) + normalize(body)).encode()).hexdigest()

# =========================
# 英語混入チェック（ASCII比率）
# =========================

def ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for c in text if ord(c) < 128) / len(text)

def is_japanese_only(text: str) -> bool:
    return ascii_ratio(text) <= ASCII_RATIO_LIMIT

# =========================
# 質問生成
# =========================

def generate_question():
    prompt = """
恋愛・人間関係の実体験相談を1件生成してください。

【条件】
・日本語のみ
・具体的な出来事と感情を含める
・タイトル20文字以上
・本文120文字以上

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""

    for _ in range(MAX_Q_RETRY):
        r = llm(prompt, max_tokens=700)
        text = r["choices"][0]["text"].strip()

        if "タイトル：" not in text or "質問：" not in text:
            continue

        title = text.split("タイトル：")[1].split("質問：")[0].strip()
        body = text.split("質問：")[1].strip()

        if len(title) < 20:
            continue
        if len(body) < 120:
            continue
        if not is_japanese_only(text):
            continue

        return title, body

    print("❌ 質問生成失敗")
    raise SystemExit(1)

# =========================
# 記事JSON生成
# =========================

def generate_article_json(question):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。
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

    required = ["lead","summary","psychology","actions","ng","misunderstanding","conclusion"]

    for _ in range(MAX_ARTICLE_RETRY):
        r = llm(prompt, max_tokens=2200)
        raw = r["choices"][0]["text"].strip()

        try:
            data = json.loads(raw)
        except:
            continue

        if not all(k in data for k in required):
            continue
        if not is_japanese_only(json.dumps(data, ensure_ascii=False)):
            continue

        return data

    print("❌ 記事JSON生成失敗")
    raise SystemExit(1)

# =========================
# 清書LLM（整形のみ）
# =========================

def clean_article_json(article):
    prompt = f"""
以下のJSON文章を清書してください。

【絶対条件】
・意味を変えない
・文を追加しない
・構成を変えない
・英語・ASCII文字を完全に除去
・JSON構造は一切変えない
・キー名は変更しない

JSON：
{json.dumps(article, ensure_ascii=False, indent=2)}
"""

    for _ in range(MAX_CLEAN_RETRY):
        r = llm(prompt, max_tokens=1200)
        raw = r["choices"][0]["text"].strip()

        try:
            cleaned = json.loads(raw)
        except:
            continue

        if not is_japanese_only(json.dumps(cleaned, ensure_ascii=False)):
            continue

        return cleaned

    print("❌ 清書フェーズ失敗")
    raise SystemExit(1)

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])

    # --- 質問生成 ---
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

    # --- 記事生成 ---
    article = generate_article_json(body)

    # --- 清書 ---
    article = clean_article_json(article)

    # --- HTML生成 ---
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
    print("✅ 完走：清書込み・英語ゼロ")

if __name__ == "__main__":
    main()
