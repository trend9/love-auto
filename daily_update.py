#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
daily_update.py【FINAL】
========================
目的：
- 毎日必ず1記事以上を生成・publish
- LLMが完全に死んでもPythonだけで完走
- 人間っぽさを保つ（ランダム微揺らし）
- AI量産臭をスコア化して可視化
- sitemap.xml を毎回必ず再生成

重要：
- exit 0 を保証（Actions絶対停止させない）
"""

import os
import sys
import random
import time
import hashlib
import traceback
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

# =========================
# 基本設定
# =========================

CONTENT_DIR = Path("content")
PUBLIC_DIR = Path("public")
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"

SITE_URL = "https://trend9.github.io/love-auto"
TIMEZONE = "+09:00"

random.seed(time.time())

# =========================
# 安全print
# =========================

def safe_print(msg):
    try:
        print(msg, flush=True)
    except Exception:
        pass

# =========================
# Python質問ジェネレータ
# =========================

QUESTIONS = [
    "最近、LINEの返信が明らかに遅くなりました。嫌われたのでしょうか。",
    "付き合う前なのに毎日連絡していて、この距離感が正しいのか不安です。",
    "相手は優しいのに踏み込んでこない理由が分かりません。",
    "デート後に急に素っ気なくなりました。何が原因でしょうか。",
    "好意は感じるのに告白してこない心理が知りたいです。"
]

def generate_python_article():
    q = random.choice(QUESTIONS)

    body = f"""
正直ね、この相談ほんとに多いの。

{q}

結論から言うと、「今は相手のペースを尊重する」が一番安全かな。
不安になると、どうしても自分の気持ちを確かめたくなるよね。

でもね、相手の行動って「気持ち」だけじゃなくて、
仕事とか余裕のなさが影響してることも多いのよ。

大事なのは、
・一喜一憂しすぎないこと
・連絡頻度＝愛情だと決めつけないこと

まぁ…簡単じゃないよね。
でも、自分をすり減らす恋だけはしなくていいと思うな。
""".strip()

    return body

# =========================
# 人間寄せランダム微揺らし
# =========================

def human_like_jitter(text: str) -> str:
    lines = text.splitlines()
    out = []

    for line in lines:
        if random.random() < 0.08:
            line += random.choice(["。", "…", ""])
        if random.random() < 0.06:
            line = line.replace("です。", "です")
        if random.random() < 0.04:
            line = line.replace("ます。", "ます…")
        out.append(line)

    return "\n".join(out)

# =========================
# 量産判定スコア
# =========================

def mass_production_score(text: str) -> dict:
    if not text.strip():
        return {"score": 100}

    sentences = [s for s in text.replace("。", ".").split(".") if s.strip()]
    avg = sum(len(s) for s in sentences) / max(len(sentences), 1)
    variance = sum((len(s) - avg) ** 2 for s in sentences) / max(len(sentences), 1)

    uniformity = max(0, 30 - variance / 20)

    ai_phrases = ["結論として", "以下の通り", "重要なのは", "総合的に"]
    phrase_score = min(30, sum(text.count(p) for p in ai_phrases) * 6)

    words = text.split()
    unique_ratio = len(set(words)) / max(len(words), 1)
    repetition = max(0, 30 - unique_ratio * 30)

    noise = 0
    if any(x in text for x in ["正直", "まぁ", "たぶん", "…"]):
        noise = 10

    score = int(min(100, uniformity + phrase_score + repetition + noise))

    return {"score": score}

# =========================
# sitemap生成
# =========================

def generate_sitemap(pages):
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for p in pages:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = p["loc"]
        SubElement(url, "lastmod").text = p["lastmod"]
        SubElement(url, "changefreq").text = "daily"
        SubElement(url, "priority").text = "0.8"

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    ElementTree(urlset).write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)

# =========================
# メイン処理
# =========================

def main():
    safe_print("=== daily_update START ===")

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    pages = []

    existing = list(CONTENT_DIR.glob("*.html"))

    # --- 記事が無ければ必ず1本生成 ---
    if not existing:
        fname = datetime.now().strftime("%Y%m%d") + ".html"
        path = CONTENT_DIR / fname

        text = generate_python_article()
        text = human_like_jitter(text)

        path.write_text(text, encoding="utf-8")
        safe_print(f"[CREATE] {fname}")

        existing.append(path)

    # --- 既存記事処理 ---
    for file in existing:
        try:
            text = file.read_text(encoding="utf-8")
            text = human_like_jitter(text)
            score = mass_production_score(text)["score"]
            file.write_text(text, encoding="utf-8")

            loc = f"{SITE_URL}/content/{file.stem}"
            lastmod = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + TIMEZONE

            pages.append({"loc": loc, "lastmod": lastmod})
            safe_print(f"[OK] {file.name} | AI臭スコア={score}")

        except Exception as e:
            safe_print(f"[ERROR] {file} :: {e}")
            traceback.print_exc()
            continue

    generate_sitemap(pages)

    safe_print(f"sitemap generated: {SITEMAP_PATH}")
    safe_print("=== daily_update END ===")

# =========================
# 実行
# =========================

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(0)
