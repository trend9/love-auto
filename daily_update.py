import os
import json
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
MAX_RETRY = 3

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

# =========================
# Article Generate (JSON保証)
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
・各文章は自然な日本語
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
    res = llm(prompt, max_tokens=3000)
    text = res["choices"][0]["text"].strip()
    return json.loads(text)

def validate_article(data: dict):
    for k, v in REQUIRED_FIELDS.items():
        if k not in data:
            raise ValueError(f"{k} が存在しません")
        if isinstance(v, int):
            if not isinstance(data[k], str) or len(data[k]) < v:
                raise ValueError(f"{k} が短すぎます")
        else:
            if not isinstance(data[k], list) or len(data[k]) < v:
                raise ValueError(f"{k} の要素数不足")

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
    today_info = today()

    article = None
    for i in range(MAX_RETRY):
        try:
            article = generate_article_struct(q["question"])
            validate_article(article)
            break
        except Exception as e:
            print(f"⚠️ 再生成 {i+1}/{MAX_RETRY}: {e}")

    if article is None:
        raise RuntimeError("記事生成に失敗しました")

    # =========================
    # 関連記事HTML生成（← ここが追加点）
    # =========================

    related_html = ""
    for r in q.get("related", []):
        related_html += (
            f'<li><a href="../{r["url"]}">{esc(r["title"])}</a></li>\n'
        )

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
           .replace("{{RELATED}}", related_html)
           .replace("{{PREV}}", "")
           .replace("{{NEXT}}", "")
           .replace("{{CANONICAL}}", "")
           .replace("{{FAQ}}", "")
    )

    save_text(os.path.join(POST_DIR, f"{q['slug']}.html"), html)

    used.append({"id": q["id"]})
    save_json(USED_PATH, used)

    print("✅ 記事生成完了（関連記事リンク込み・全文保証）")

if __name__ == "__main__":
    main()
