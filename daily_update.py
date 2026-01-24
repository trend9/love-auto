import os
import json
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
MAX_RETRY = 3

# =========================
# LLM（★1回ロード）
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
    n = datetime.now()
    return {
        "iso": n.isoformat(),
        "jp": n.strftime("%Y年%m月%d日")
    }

# =========================
# Article Generate（JSON保証）
# =========================

REQUIRED = {
    "lead": 80,
    "summary": 120,
    "psychology": 150,
    "actions": 3,
    "ng": 2,
    "misunderstanding": 100,
    "conclusion": 120
}

def generate_article(question):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下のJSONを**完全に埋めて**ください。
JSON以外は出力禁止。

{{
  "lead": "",
  "summary": "",
  "psychology": "",
  "actions": ["", "", ""],
  "ng": ["", ""],
  "misunderstanding": "",
  "conclusion": ""
}}

【相談】
{question}
"""
    r = llm(prompt, max_tokens=2800)
    return json.loads(r["choices"][0]["text"].strip())

def validate(d):
    for k, v in REQUIRED.items():
        if k not in d:
            raise ValueError(k)
        if isinstance(v, int):
            if len(d[k]) < v:
                raise ValueError(k)
        else:
            if len(d[k]) < v:
                raise ValueError(k)

# =========================
# Main
# =========================

def main():
    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_PATH, [])

    used_ids = {u["id"] for u in used}
    unused = [q for q in questions if q["id"] not in used_ids]

    if not unused:
        raise RuntimeError("未使用質問が存在しない（設計違反）")

    q = unused[0]
    today_info = today()

    article = None
    for _ in range(MAX_RETRY):
        try:
            article = generate_article(q["question"])
            validate(article)
            break
        except:
            continue

    if article is None:
        raise RuntimeError("記事生成失敗")

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    html = (
        tpl.replace("{{TITLE}}", esc(q["title"]))
           .replace("{{META_DESCRIPTION}}", esc(q["question"][:120]))
           .replace("{{DATE_ISO}}", today_info["iso"])
           .replace("{{DATE_JP}}", today_info["jp"])
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{q['slug']}.html")
           .replace("{{LEAD}}", esc(article["lead"]))
           .replace("{{QUESTION}}", esc(q["question"]))
           .replace("{{SUMMARY_ANSWER}}", esc(article["summary"]))
           .replace("{{PSYCHOLOGY}}", esc(article["psychology"]))
           .replace("{{ACTION_LIST}}", "\n".join(f"<li>{esc(a)}</li>" for a in article["actions"]))
           .replace("{{NG_LIST}}", "\n".join(f"<li>{esc(n)}</li>" for n in article["ng"]))
           .replace("{{MISUNDERSTANDING}}", esc(article["misunderstanding"]))
           .replace("{{CONCLUSION}}", esc(article["conclusion"]))
    )

    save_text(os.path.join(POST_DIR, f"{q['slug']}.html"), html)

    used.append({"id": q["id"]})
    save_json(USED_PATH, used)

    print("✅ 記事生成完了")

if __name__ == "__main__":
    main()
