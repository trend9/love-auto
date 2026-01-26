#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POSTS_DIR = BASE_DIR / "posts"

QUESTION_PATH = DATA_DIR / "questions.json"
POSTS_DIR.mkdir(exist_ok=True)

LLAMA_BIN = BASE_DIR / "llama"
MODEL_PATH = BASE_DIR / "models" / "llama-q4km.gguf"


def log(msg):
    print(f"[daily_update] {msg}", flush=True)


# ===== 質問読み込み（list固定）=====
def load_questions():
    if not QUESTION_PATH.exists():
        raise FileNotFoundError("questions.json not found")

    data = json.loads(QUESTION_PATH.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise TypeError("questions.json must be list")

    return data


# ===== slug生成（従来形式維持）=====
def make_slug(date_str: str, question: str) -> str:
    safe = re.sub(r"[^\wぁ-んァ-ン一-龥]+", "", question)
    return f"{date_str}-{safe}"


# ===== LLM呼び出し =====
def call_llm(prompt: str) -> str:
    if not LLAMA_BIN.exists() or not MODEL_PATH.exists():
        log("llama not found -> fallback html")
        return fallback_html(prompt)

    try:
        proc = subprocess.run(
            [
                str(LLAMA_BIN),
                "-m", str(MODEL_PATH),
                "-p", prompt,
                "--ctx-size", "2048",
                "--temp", "0.7",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        out = proc.stdout.strip()
        if "<html" not in out.lower():
            raise ValueError("invalid html output")
        return out

    except Exception as e:
        log(f"llm error: {e}")
        return fallback_html(prompt)


# ===== フォールバックHTML（必ずSEO構造）=====
def fallback_html(question: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>{question}</title>
<meta name="description" content="{question}">
</head>
<body>
<article>
<h1>{question}</h1>

<section>
<h2>結論</h2>
<p>片思いで胸が苦しくなるのは自然な感情です。大切なのは、相手との距離を一歩ずつ縮める行動を取ることです。</p>
</section>

<section>
<h2>なぜこのような気持ちになるのか</h2>
<p>好意を抱く相手との関係性が不確かなとき、不安や緊張が強まりやすくなります。</p>
</section>

<section>
<h2>具体的な行動ステップ</h2>
<ul>
<li>まずは挨拶や短い会話を増やす</li>
<li>相手の話をよく聞く</li>
<li>焦らず自然な距離感を保つ</li>
</ul>
</section>

<section>
<h2>まとめ</h2>
<p>無理に結果を求めず、信頼関係を築くことが最優先です。</p>
</section>

</article>
</body>
</html>
"""


def save_article(slug: str, html: str):
    path = POSTS_DIR / f"{slug}.html"
    path.write_text(html, encoding="utf-8")
    log(f"saved: {path.name}")


# ===== main =====
def main():
    log("=== daily_update START ===")

    questions = load_questions()

    # 最新の未使用質問を1つだけ処理
    target = None
    for q in reversed(questions):
        if not q.get("used"):
            target = q
            break

    if not target:
        log("no unused question")
        return

    question_text = target["question"]
    today = datetime.now().strftime("%Y-%m-%d")
    slug = make_slug(today, question_text)

    prompt = f"""
以下の質問に対して、日本語でSEO最適化されたHTML記事を全文生成してください。

条件：
- <!DOCTYPE html> から </html> まで全文
- article構造
- h1は1つ（質問文）
- h2,h3を論理的に使用
- 結論を最初に書く
- 翻訳・英語不要

質問：
{question_text}
"""

    html = call_llm(prompt)
    save_article(slug, html)

    # used フラグ更新
    target["used"] = True
    QUESTION_PATH.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log("=== daily_update END ===")


if __name__ == "__main__":
    main()
