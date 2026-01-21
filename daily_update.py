import json
import os
import datetime
import random
from llama_cpp import Llama

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POST_DIR = os.path.join(BASE_DIR, "posts")
DATA_DIR = os.path.join(BASE_DIR, "data")
QUESTIONS_JSON = os.path.join(DATA_DIR, "questions.json")
POST_TEMPLATE = os.path.join(BASE_DIR, "post_template.html")

MAX_INDEX_ITEMS = 10        # ← index に表示する最新件数
RELATED_LINKS = 3           # ← 記事下に出す内部リンク数

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(QUESTIONS_JSON):
    with open(QUESTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

with open(QUESTIONS_JSON, "r", encoding="utf-8") as f:
    past = json.load(f)

llm = Llama(
    model_path="./models/model.gguf",
    n_ctx=1024,
    n_threads=4
)

now = datetime.datetime.now()
date_str = now.strftime("%Y/%m/%d %H:%M")
file_stamp = now.strftime("%Y%m%d_%H%M%S")

# ======================
# テーマ生成（被り防止）
# ======================
past_titles = [p["title"] for p in past][-20:]

theme_prompt = f"""
20〜30代女性向けの恋愛相談テーマを1つだけ出してください。
過去と被らないこと。

過去テーマ:
{past_titles}

条件:
・短い日本語
・感情が伝わる
・タイトルのみ
"""

theme = llm(theme_prompt, max_tokens=64)["choices"][0]["text"].strip()

# ======================
# お便り
# ======================
letter_prompt = f"""
次のテーマでラジオ相談のお便りを書いてください。

テーマ: {theme}

条件:
・ラジオネームあり（◯◯ちゃん）
・一人称
・300〜400文字
"""

letter = llm(letter_prompt, max_tokens=600)["choices"][0]["text"].strip()

# ======================
# 回答
# ======================
answer_prompt = f"""
あなたは恋愛相談ラジオの回答者「結姉さん」です。

構成:
1. 共感
2. 悩みの核心
3. 視点の転換
4. 優しい一言

禁止:
・説教
・〜すべき
・専門用語

相談内容:
{letter}
"""

answer = llm(answer_prompt, max_tokens=700)["choices"][0]["text"]
answer = answer.replace("【回答文】", "").strip()

# ======================
# メタ description
# ======================
meta_prompt = f"""
次の記事のメタディスクリプションを書いてください。

条件:
・120文字以内
・安心感
・SEOタイトル等は含めない
"""

meta = llm(meta_prompt, max_tokens=150)["choices"][0]["text"].strip()

# ======================
# ラジオネーム抽出
# ======================
name = "匿名"
for line in letter.splitlines():
    if "ちゃん" in line:
        name = line.strip()
        break

# ======================
# 内部リンク生成
# ======================
related_html = ""
if len(past) >= RELATED_LINKS:
    related = random.sample(past, RELATED_LINKS)
    related_html += "<ul class='related-posts'>"
    for r in related:
        related_html += f"<li><a href='../{r['url']}'>{r['title']}</a></li>"
    related_html += "</ul>"

# ======================
# HTML生成
# ======================
with open(POST_TEMPLATE, "r", encoding="utf-8") as f:
    tpl = f.read()

html = (
    tpl.replace("{{TITLE}}", theme)
       .replace("{{META}}", meta)
       .replace("{{DATE}}", date_str)
       .replace("{{NAME}}", name)
       .replace("{{LETTER}}", letter)
       .replace("{{ANSWER}}", answer)
       .replace("{{RELATED}}", related_html)
)

post_filename = f"{file_stamp}.html"
with open(os.path.join(POST_DIR, post_filename), "w", encoding="utf-8") as f:
    f.write(html)

# ======================
# questions.json 更新（最新が先頭）
# ======================
past.insert(0, {
    "title": theme,
    "url": f"posts/{post_filename}",
    "date": date_str,
    "description": meta
})

with open(QUESTIONS_JSON, "w", encoding="utf-8") as f:
    json.dump(past, f, ensure_ascii=False, indent=2)

print("生成完了:", post_filename)
