import os
import json
import re
import hashlib
from datetime import datetime
from llama_cpp import Llama

# =========================
# Paths
# =========================

MODEL_PATH = "./models/model.gguf"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
QUESTIONS_PATH = "data/questions.json"
SITE_URL = "https://trend9.github.io/love-auto"

MAX_CONTEXT = 4096

# =========================
# LLM（1回ロード）
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    temperature=0.85,
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

def esc(t: str) -> str:
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

def contains_english(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))

# =========================
# Question Generate（必ず成功）
# =========================

def generate_question():
    while True:
        prompt = """
恋愛・人間関係の実体験相談を1件生成してください。

【条件】
・日本語のみ（英語禁止）
・具体的な出来事と感情を含める
・タイトル20文字以上
・本文120文字以上
・説明文・注釈・例は禁止

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""
        r = llm(prompt, max_tokens=700)
        text = r["choices"][0]["text"].strip()

        if "タイトル：" not in text or "質問：" not in text:
            continue

        title = text.split("タイトル：")[1].split("質問：")[0].strip()
        body = text.split("質問：")[1].strip()

        if len(title) < 20 or len(body) < 120:
            continue

        if contains_english(title + body):
            continue

        return title, body

# =========================
# Article Generate（一次生成・多少雑OK）
# =========================

def generate_article_raw(question):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下のJSONを出力してください。
多少文章が荒くても構いません。

【JSON】
{{
  "lead": "導入文",
  "summary": "結論",
  "psychology": "相手の心理",
  "actions": ["行動1", "行動2", "行動3"],
  "ng": ["NG1", "NG2"],
  "misunderstanding": "よくある誤解",
  "conclusion": "まとめ"
}}

相談内容：
{question}
"""
    r = llm(prompt, max_tokens=2200)
    return r["choices"][0]["text"].strip()

# =========================
# Article Rewrite（清書・品質保証）
# =========================

def rewrite_article_clean(raw_json_text, question):
    prompt = f"""
以下はAIが生成した恋愛相談記事JSONです。

【必須ルール】
・日本語のみ（英語があれば完全削除）
・注釈、例文、説明文、生成痕跡は全削除
・意味を変えず自然な日本語に清書
・SEO向けに読みやすく整理
・JSON形式厳守
・各項目は十分な文字量で書き直す

【JSON形式】
{{
  "lead": "80文字以上",
  "summary": "120文字以上",
  "psychology": "150文字以上",
  "actions": ["具体行動1", "具体行動2", "具体行動3"],
  "ng": ["避けたい行動1", "避けたい行動2"],
  "misunderstanding": "100文字以上",
  "conclusion": "120文字以上"
}}

【相談内容】
{question}

【元JSON】
{raw_json_text}
"""
    r = llm(prompt, max_tokens=2600)
    text = r["choices"][0]["text"].strip()
    return json.loads(text)

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])

    # ① 質問生成
    title, body = generate_question()
    slug = slugify_jp(title)
    qid = uid()

    question = {
        "id": qid,
        "title": title,
        "slug": slug,
        "question": body,
        "created_at": today()["iso"],
        "content_hash": content_hash(title, body),
        "url": f"posts/{slug}.html"
    }

    questions.append(question)
    save_json(QUESTIONS_PATH, questions)

    # ② 記事生成 → 清書
    raw_article = generate_article_raw(body)
    article = rewrite_article_clean(raw_article, body)

    # ③ HTML生成
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

    print("✅ 完全自動・安定生成（清書込み）完了")

if __name__ == "__main__":
    main()
