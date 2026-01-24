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
        body = body.split("【生成】")[0].strip()

        if len(title) >= 20 and len(body) >= 120:
            return title, body

# =========================
# Article Generate（完全耐性）
# =========================

def extract_json(text: str) -> dict | None:
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except:
        return None

def generate_article(question):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下のJSONをすべて埋めて出力してください。

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
    r = llm(prompt, max_tokens=2600)
    raw = r["choices"][0]["text"]

    data = extract_json(raw)

    # ---- 最終保険（絶対に落とさない）----
    if not isinstance(data, dict):
        data = {}

    data.setdefault("lead", question[:120])
    data.setdefault("summary", question)
    data.setdefault("psychology", "相手にも迷いや不安があり、距離感を測りかねている可能性があります。")
    data.setdefault("actions", [
        "感情を整理してから落ち着いて話す",
        "相手の立場を尊重した言葉を選ぶ",
        "関係を急がず時間を味方につける"
    ])
    data.setdefault("ng", [
        "感情的に結論を急ぐ",
        "相手の沈黙を悪意だと決めつける"
    ])
    data.setdefault("misunderstanding", "相手の態度が変わったからといって、気持ちが完全に離れたとは限りません。")
    data.setdefault("conclusion", "焦らず自分の気持ちを大切にしながら、少しずつ関係を見直していきましょう。")

    return data

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])

    title, body = generate_question()
    slug = slugify_jp(title)
    qid = uid()

    questions.append({
        "id": qid,
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

    print("✅ 完全自動・Actions安定版 完了")

if __name__ == "__main__":
    main()
