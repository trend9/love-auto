import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# =========================
# 設定
# =========================

QUESTIONS_FILE = "data/questions.json"
USED_QUESTIONS_FILE = "data/used_questions.json"

POSTS_DIR = Path("posts")
TEMPLATE_FILE = "post_template.html"

POSTS_DIR.mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# =========================
# JSON ユーティリティ
# =========================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# HTML生成
# =========================

def generate_post_html(title: str) -> str:
    """
    記事1ページ構成（固定）
    """
    now = datetime.now().strftime("%Y-%m-%d")

    content = f"""
<p class="yui-answer">
好きだからこそ悩んでしまうよね。
その気持ちはとても自然なものだよ。
焦らず、一緒に整理していこう。
</p>

<h2>この悩みが起きる理由</h2>
<p>
恋愛では「相手の気持ちが見えない不安」や
「自分ばかり好きなのでは」という感情が
大きくなりやすいんだ。
</p>

<h3>よくある勘違い</h3>
<p>
LINEの頻度や態度だけで
相手の本音を判断してしまうこと。
</p>

<h2>今できる具体的な行動</h2>
<p>
一度、自分の気持ちを整理してから
相手と自然に会話する時間を作ろう。
</p>

<h3>やってはいけない行動</h3>
<p>
不安なまま詰め寄ること。
これは逆効果になりやすいよ。
</p>
"""

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    return template \
        .replace("{{TITLE}}", title) \
        .replace("{{DATE}}", now) \
        .replace("{{CONTENT}}", content)

# =========================
# メイン処理
# =========================

def main():
    # ① 質問生成（無限化ロジック）
    subprocess.run(
        ["python3", "question_generator.py"],
        check=True
    )

    questions = load_json(QUESTIONS_FILE, [])
    used = load_json(USED_QUESTIONS_FILE, [])

    used_titles = {q["title"] for q in used if "title" in q}

    # ② 未使用の質問を1つ選ぶ
    target = None
    for q in questions:
        if q["title"] not in used_titles:
            target = q
            break

    if not target:
        print("⚠ 未使用の質問がありません")
        return

    title = target["title"]

    # ③ HTML生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = POSTS_DIR / f"{timestamp}.html"

    html = generate_post_html(title)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    # ④ 使用済みへ移動
    used.append({
        "title": title,
        "used_at": datetime.now().isoformat()
    })

    save_json(USED_QUESTIONS_FILE, used)

    print(f"✅ 記事生成完了: {filename}")

# =========================

if __name__ == "__main__":
    main()
