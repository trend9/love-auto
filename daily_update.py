#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUESTION_FILE = BASE_DIR / "data" / "questions.json"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ===== LLM設定 =====
LLAMA_BIN = BASE_DIR / "llama"          # llama.cpp バイナリ（無い環境も想定）
MODEL_PATH = BASE_DIR / "models" / "llama-q4km.gguf"

# ===== ユーティリティ =====
def log(msg):
    print(f"[daily_update] {msg}", flush=True)

def load_questions():
    if not QUESTION_FILE.exists():
        log("questions.json not found")
        return []

    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("questions", [])

def save_article(slug: str, html: str):
    out = OUTPUT_DIR / f"{slug}.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"saved: {out.name}")

# ===== LLM呼び出し =====
def call_llm(prompt: str) -> str:
    """
    llama.cpp が存在しない / model が無い場合でも
    CI を落とさないための安全実装
    """

    if not LLAMA_BIN.exists():
        log("llama binary not found -> fallback mode")
        return fallback_response(prompt)

    if not MODEL_PATH.exists():
        log("model file not found -> fallback mode")
        return fallback_response(prompt)

    try:
        proc = subprocess.run(
            [
                str(LLAMA_BIN),
                "-m", str(MODEL_PATH),
                "-p", prompt,
                "--ctx-size", "2048",
                "--temp", "0.7"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return proc.stdout.strip()

    except Exception as e:
        log(f"llm error: {e}")
        return fallback_response(prompt)

def fallback_response(prompt: str) -> str:
    """
    LLMが使えない場合でも
    SEO構造HTMLを必ず返す
    """

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>【自動生成】{prompt[:30]}</title>
<meta name="description" content="{prompt[:60]}">
</head>
<body>
<article>
<h1>{prompt}</h1>

<section>
<h2>結論</h2>
<p>このページは現在AI生成のフォールバックモードで生成されています。</p>
</section>

<section>
<h2>理由</h2>
<p>LLM実行環境が未構築、もしくはモデルファイルが存在しないためです。</p>
</section>

<section>
<h2>対策</h2>
<ul>
<li>llama.cpp バイナリの配置</li>
<li>GGUFモデルの配置</li>
<li>CI環境変数の見直し</li>
</ul>
</section>

</article>
</body>
</html>
"""

# ===== メイン処理 =====
def main():
    log("=== daily_update START ===")

    questions = load_questions()
    if not questions:
        log("no questions found")
        return

    for q in questions:
        qid = q.get("id")
        title = q.get("title")

        if not qid or not title:
            continue

        slug = f"q{qid}_{datetime.now().strftime('%Y%m%d')}"

        prompt = f"""
以下の質問に対して、
SEO最適化されたHTML記事を全文で生成してください。

条件：
- <article> 構造
- h1は1つのみ
- h2,h3を論理的に使用
- 結論を最初に書く
- 日本語
- HTML全文のみ出力

質問：
{title}
"""

        log(f"generate: {slug}")
        html = call_llm(prompt)
        save_article(slug, html)

    log("=== daily_update END ===")

if __name__ == "__main__":
    main()
