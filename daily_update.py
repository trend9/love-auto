import os
import json
import random
from datetime import datetime
from llama_cpp import Llama

# =========================
# 基本設定（※ここだけ環境依存）
# =========================

MODEL_PATH = "./models/model.gguf"
POST_DIR = "./posts"
TEMPLATE_PATH = "./template/article.html"
QUESTION_POOL_PATH = "./data/questions.json"

AUTHOR_NAME = "結姉さん"

# =========================
# LLM 初期化
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    temperature=0.85,
    top_p=0.9,
)

# =========================
# ユーティリティ
# =========================

def load_questions():
    with open(QUESTION_POOL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_template():
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

def today():
    now = datetime.now()
    return {
        "iso": now.strftime("%Y-%m-%d"),
        "jp": now.strftime("%Y年%m月%d日"),
        "slug": now.strftime("%Y%m%d"),
    }

# =========================
# LLM生成
# =========================

def llm_generate(prompt):
    result = llm(
        prompt,
        max_tokens=2048,
        stop=["</html>"]
    )
    return result["choices"][0]["text"].strip()

def generate_article(question_text):
    prompt = f"""
あなたは恋愛相談に答える日本人女性AI「結姉さん」です。

以下の相談内容をもとに、
SEOを意識しつつ、人間味があり、共感が強く、
h2・h3構造が自然に含まれた長文記事を書いてください。

【絶対条件】
・説教しない
・感情を肯定する
・断定しすぎない
・現実的な行動を提示
・検索ユーザーが「これ知りたかった」と感じる構成

【相談内容】
{question_text}

【出力項目】
- タイトル
- メタディスクリプション
- 導入文
- 結論
- 相手の心理
- 今できる具体的な行動（箇条書き）
- 避けたい行動（箇条書き）
- よくある勘違い
- まとめ
"""
    return llm_generate(prompt)

# =========================
# HTML埋め込み
# =========================

def build_html(template, article_data, question_text):
    today_info = today()

    html = template
    html = html.replace("{{TITLE}}", article_data["title"])
    html = html.replace("{{META_DESCRIPTION}}", article_data["meta_description"])
    html = html.replace("{{DATE_ISO}}", today_info["iso"])
    html = html.replace("{{DATE_JP}}", today_info["jp"])
    html = html.replace("{{PAGE_URL}}", f"https://example.com/posts/{today_info['slug']}.html")
    html = html.replace("{{LEAD}}", article_data["lead"])
    html = html.replace("{{QUESTION}}", question_text)
    html = html.replace("{{SUMMARY_ANSWER}}", article_data["summary"])
    html = html.replace("{{PSYCHOLOGY}}", article_data["psychology"])
    html = html.replace("{{ACTION_LIST}}", article_data["actions"])
    html = html.replace("{{NG_LIST}}", article_data["ng"])
    html = html.replace("{{MISUNDERSTANDING}}", article_data["misunderstanding"])
    html = html.replace("{{CONCLUSION}}", article_data["conclusion"])
    html = html.replace("{{RELATED}}", "")
    html = html.replace("{{PREV}}", "")
    html = html.replace("{{NEXT}}", "")
    html = html.replace("{{CANONICAL}}", "")
    html = html.replace("{{FAQ}}", "")

    return html

# =========================
# メイン処理
# =========================

def main():
    os.makedirs(POST_DIR, exist_ok=True)

    questions = load_questions()
    question = random.choice(questions)

    raw_article = generate_article(question)

    # 想定：LLM出力をJSON化（最低限）
    article_data = json.loads(raw_article)

    template = load_template()
    html = build_html(template, article_data, question)

    filename = f"{today()['slug']}.html"
    path = os.path.join(POST_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {path}")

if __name__ == "__main__":
    main()
