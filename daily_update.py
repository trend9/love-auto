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

# =========================
# Question Generate（必ず成功）
# =========================

def generate_question():
    while True:
        prompt = """
恋愛・人間関係の実体験相談を1件生成してください。

【条件】
・具体的な出来事と感情を含める
・タイトル20文字以上
・本文120文字以上
・説明文や補足は禁止

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

        # 生成ゴミ除去
        body = body.split("【生成】")[0].strip()

        if len(title) >= 20 and len(body) >= 120:
            return title, body

# =========================
# Article Generate（JSON保証＋保険）
# =========================

def generate_article(question):
    for _ in range(3):
        try:
            prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下のJSONを必ずすべて埋めて出力してください。
JSON以外は禁止。

{{
  "lead": "読者の感情を代弁する導入文（80文字以上・疑問文禁止）",
  "summary": "結論（120文字以上）",
  "psychology": "相手の心理解説（150文字以上）",
  "actions": ["具体行動1", "具体行動2", "具体行動3"],
  "ng": ["避けたい行動1", "避けたい行動2"],
  "misunderstanding": "よくある誤解（100文字以上）",
  "conclusion": "まとめ（120文字以上）"
}}

相談内容：
{question}
"""
            r = llm(prompt, max_tokens=2600)
            article = json.loads(r["choices"][0]["text"])

            # NG保険
            if len(article.get("ng", [])) < 2:
                article.setdefault("ng", []).append(
                    "相手の気持ちを決めつけて行動してしまう"
                )

            return article
        except:
            continue

    raise RuntimeError("記事生成失敗")

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])

    # ① 質問生成（常に新規）
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

    # ② 記事生成
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
           .replace(
               "{{ACTION_LIST}}",
               "\n".join(f"<li>{esc(a)}</li>" for a in article["actions"])
           )
           .replace(
               "{{NG_LIST}}",
               "\n".join(f"<li>{esc(n)}</li>" for n in article["ng"])
           )
           .replace("{{MISUNDERSTANDING}}", esc(article["misunderstanding"]))
           .replace("{{CONCLUSION}}", esc(article["conclusion"]))
           .replace("{{RELATED}}", "")
           .replace("{{PREV}}", "")
           .replace("{{NEXT}}", "")
           .replace("{{CANONICAL}}", "")
           .replace("{{FAQ}}", "")
    )

    save_text(os.path.join(POST_DIR, f"{slug}.html"), html)

    print("✅ 完全自動・安定生成 完了")

if __name__ == "__main__":
    main()
