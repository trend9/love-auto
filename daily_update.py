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

QUESTIONS_PATH = "data/questions.json"
USED_PATH = "data/used_questions.json"

POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
SITE_URL = "https://trend9.github.io/love-auto"

MAX_CONTEXT = 4096
MAX_RETRY = 5

# =========================
# LLM（single-process / 1回ロード）
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    temperature=0.85,
    top_p=0.9,
    repeat_penalty=1.15,
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
# Question Generate（絶対に落ちない最終版）
# =========================

def generate_question():
    base_prompt = """
あなたは「恋愛・人間関係の実体験相談」を1件だけ生成してください。

【厳守】
・抽象論、テンプレ禁止
・具体的な期間／関係性／出来事を含める
・感情の葛藤を必ず入れる

【形式】
タイトル：〇〇〇
質問：〇〇〇
"""

    phases = [
        {"title": 20, "body": 120},  # 理想
        {"title": 15, "body": 80},   # 現実
        {"title": 10, "body": 50},   # 最終保険
    ]

    for phase in phases:
        for _ in range(MAX_RETRY):
            r = llm(base_prompt, max_tokens=700)
            text = r["choices"][0]["text"].strip()

            if "タイトル：" not in text or "質問：" not in text:
                continue

            title = text.split("タイトル：")[1].split("質問：")[0].strip()
            body = text.split("質問：")[1].strip()

            if len(title) >= phase["title"] and len(body) >= phase["body"]:
                return title, body

    # 🔥 ここには基本来ないが、Actions絶対停止防止
    return (
        "付き合って3年の彼との将来に不安を感じ始めた理由",
        "付き合って3年になる彼がいます。最近、結婚や将来の話をすると話題を変えられることが増え、不安を感じるようになりました。彼のことは好きですが、このまま時間だけが過ぎていくのではないかと焦っています。どう向き合えばいいのか分かりません。"
    )

# =========================
# Article Generate（JSON完全保証）
# =========================

REQUIRED_FIELDS = {
    "lead": 80,
    "summary": 120,
    "psychology": 150,
    "actions": 3,
    "ng": 2,
    "misunderstanding": 100,
    "conclusion": 120
}

def generate_article_struct(question: str) -> dict:
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下のJSONを**必ずすべて埋めて**出力してください。
1つでも欠けたら失敗です。

【厳守】
・JSON以外は出力しない
・説教しない／断定しない
・共感と具体例重視

【JSON形式】
{{
  "lead": "導入文（80文字以上）",
  "summary": "結論（120文字以上）",
  "psychology": "相手の心理解説（150文字以上）",
  "actions": ["具体行動1", "具体行動2", "具体行動3"],
  "ng": ["避けたい行動1", "避けたい行動2"],
  "misunderstanding": "よくある誤解（100文字以上）",
  "conclusion": "まとめ（120文字以上）"
}}

【相談内容】
{question}
"""
    r = llm(prompt, max_tokens=2800)
    return json.loads(r["choices"][0]["text"].strip())

def validate_article(data: dict):
    for k, v in REQUIRED_FIELDS.items():
        if k not in data:
            raise ValueError(f"{k} 欠落")
        if isinstance(v, int):
            if not isinstance(data[k], str) or len(data[k]) < v:
                raise ValueError(f"{k} 短すぎ")
        else:
            if not isinstance(data[k], list) or len(data[k]) < v:
                raise ValueError(f"{k} 要素不足")

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_PATH, [])

    used_ids = {u["id"] for u in used}
    hashes = {q["content_hash"] for q in questions}

    # --- 常に質問を生成 ---
    title, body = generate_question()
    h = content_hash(title, body)

    if h in hashes:
        print("ℹ️ 重複質問検知 → スキップ")
        return

    slug = slugify_jp(title)
    qid = uid()

    question = {
        "id": qid,
        "title": title,
        "slug": slug,
        "question": body,
        "created_at": today()["iso"],
        "content_hash": h,
        "url": f"posts/{slug}.html"
    }

    questions.append(question)
    save_json(QUESTIONS_PATH, questions)

    # --- 記事生成 ---
    article = None
    for i in range(MAX_RETRY):
        try:
            article = generate_article_struct(body)
            validate_article(article)
            break
        except Exception as e:
            print(f"⚠️ 記事再生成 {i+1}/{MAX_RETRY}: {e}")

    if article is None:
        raise RuntimeError("記事生成失敗")

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    today_info = today()

    html = (
        tpl.replace("{{TITLE}}", esc(title))
           .replace("{{META_DESCRIPTION}}", esc(body[:120]))
           .replace("{{DATE_ISO}}", today_info["iso"])
           .replace("{{DATE_JP}}", today_info["jp"])
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

    used.append({"id": qid})
    save_json(USED_PATH, used)

    print("✅ 記事生成完了（single-process / 絶対停止しない）")

if __name__ == "__main__":
    main()
