import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from llama_cpp import Llama

# =========================
# パス設定
# =========================
MODEL_PATH = "./models/model.gguf"
QUESTIONS_PATH = "data/questions.json"
POST_TEMPLATE_PATH = "post_template.html"
POST_DIR = "posts"
ARCHIVE_PATH = "archive.html"
INDEX_PATH = "index.html"

# =========================
# LLM 初期化（記事生成用）
# =========================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=os.cpu_count() or 4,
    n_gpu_layers=0,
    verbose=False
)

# =========================
# ユーティリティ
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def safe(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# =========================
# 記事生成プロンプト
# =========================
def build_article_prompt(title, question):
    return f"""
あなたは「ゆい姉さん」という恋愛相談サイトの回答者です。
以下の相談に対して、誠実で実用的なアドバイス記事を書いてください。

条件：
- 日本語
- 上から目線・説教口調は禁止
- 具体的・現実的なアドバイス
- 文字数はしっかり（短文禁止）
- 絵文字・記号は禁止
- 見出し構成を必ず守る

構成（厳守）：

最初に3〜4行で全体の要点をまとめる（ゆい姉さんの語り）

<h2>今の気持ちを整理しよう</h2>
感情の整理と状況の言語化

<h2>なぜその悩みが生まれるのか</h2>
心理的背景・よくあるケース

<h2>ゆい姉さんからの具体的アドバイス</h2>

<h3>まず意識してほしいこと</h3>
<h3>相手との向き合い方</h3>
<h3>やってはいけない行動</h3>

<h2>それでも迷ったときの考え方</h2>
背中を押す締め

相談内容：
{question}
"""

# =========================
# 記事本文生成
# =========================
def generate_article(title, question):
    result = llm(
        build_article_prompt(title, question),
        max_tokens=1800,
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["</s>"]
    )
    return result["choices"][0]["text"].strip()

# =========================
# メイン処理
# =========================
def main():
    # ① 先に質問を補充（Bを実行）
    subprocess.run(["python3", "question_generator.py"], check=True)

    questions = load_json(QUESTIONS_PATH)
    if not questions:
        print("⚠ 質問が存在しません")
        return

    # ② 最新の未生成質問を取得
    latest = questions[-1]

    post_id = latest["id"]
    title = latest["title"]
    question = latest["question"]
    url = latest["url"]

    # ③ 記事生成
    article_html = generate_article(title, question)

    # ④ テンプレ読み込み
    with open(POST_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # ⑤ 前後ナビ生成
    idx = len(questions) - 1
    prev_link = ""
    next_link = ""

    if idx > 0:
        p = questions[idx - 1]
        prev_link = f'<a href="../{p["url"]}">← 前の記事</a>'

    if idx < len(questions) - 1:
        n = questions[idx + 1]
        next_link = f'<a href="../{n["url"]}">次の記事 →</a>'

    # ⑥ 関連記事（直近3件）
    related = ""
    for q in reversed(questions[max(0, idx-3):idx]):
        related += f'<li><a href="../{q["url"]}">{safe(q["title"])}</a></li>\n'

    # ⑦ HTML 組み立て
    html = template \
        .replace("{{TITLE}}", safe(title)) \
        .replace("{{QUESTION}}", safe(question)) \
        .replace("{{CONTENT}}", article_html) \
        .replace("{{PREV}}", prev_link) \
        .replace("{{NEXT}}", next_link) \
        .replace("{{RELATED}}", related)

    # ⑧ 保存
    save_text(os.path.join(POST_DIR, f"{post_id}.html"), html)

    # =========================
    # archive.html 再生成
    # =========================
    archive_items = ""
    for q in reversed(questions):
        archive_items += f'<li><a href="{q["url"]}">{safe(q["title"])}</a></li>\n'

    archive_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>相談アーカイブ</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>相談アーカイブ</h1>
<ul class="archive-list">
{archive_items}
</ul>
</body>
</html>
"""
    save_text(ARCHIVE_PATH, archive_html)

    print("✅ 記事・アーカイブ生成完了")

if __name__ == "__main__":
    main()
