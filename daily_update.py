import os
import json
import random
import subprocess
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

# =========================
# LLM
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MAX_CONTEXT,
    temperature=0.85,
    top_p=0.9,
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

# =========================
# Article Generate
# =========================

def generate_article(question):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

SEOを意識しつつ、
人間味があり、共感が強く、
h2・h3構造が自然な長文記事を書いてください。

【条件】
・説教しない
・断定しない
・感情を言語化
・具体例を多く
・HTMLタグ以外は出力しない

【相談内容】
{question}
"""
    r = llm(prompt, max_tokens=3000)
    return r["choices"][0]["text"].strip()

# =========================
# Main
# =========================

def main():
    # 質問生成
    subprocess.run(["python", "question_generator.py"], check=False)

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_PATH, [])

    used_ids = {u["id"] for u in used}
    unused = [q for q in questions if q["id"] not in used_ids]

    if not unused:
        raise RuntimeError("未使用の質問がありません")

    q = unused[0]

    article_html = generate_article(q["question"])
    today_info = today()

    with open(POST_TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    html = (
        tpl.replace("{{TITLE}}", esc(q["title"]))
           .replace("{{META_DESCRIPTION}}", esc(q["question"][:120]))
           .replace("{{DATE_ISO}}", today_info["iso"])
           .replace("{{DATE_JP}}", today_info["jp"])
           .replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{q['slug']}.html")
           .replace("{{LEAD}}", "")
           .replace("{{QUESTION}}", esc(q["question"]))
           .replace("{{SUMMARY_ANSWER}}", "")
           .replace("{{PSYCHOLOGY}}", "")
           .replace("{{ACTION_LIST}}", "")
           .replace("{{NG_LIST}}", "")
           .replace("{{MISUNDERSTANDING}}", "")
           .replace("{{CONCLUSION}}", "")
           .replace("{{RELATED}}", "")
           .replace("{{PREV}}", "")
           .replace("{{NEXT}}", "")
           .replace("{{CANONICAL}}", "")
           .replace("{{FAQ}}", "")
    )

    html = html.replace("{{CONTENT}}", article_html)

    save_text(os.path.join(POST_DIR, f"{q['slug']}.html"), html)

    used.append({"id": q["id"]})
    save_json(USED_PATH, used)

    print("✅ 記事生成完了")

if __name__ == "__main__":
    main()
