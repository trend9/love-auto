#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
daily_update.py【FINAL / MULTI GENERATE】
"""

import os
import sys
import random
import time
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

# 1日に生成したい記事数（最低保証）
DAILY_GENERATE_COUNT = 2  # ←ここを増やせば量産可能

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
# 質問ジェネレータ
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

    return f"""
正直ね、この相談ほんとに多いの。

{q}

結論から言うと、「今は相手のペースを尊重する」が一番安全かな。

不安になると、どうしても相手の気持ちを確かめたくなるよね。
でもね、連絡の頻度って、気持ちだけじゃなくて
余裕のなさが原因なことも本当に多いの。

大事なのは、
・一喜一憂しすぎないこと
・相手の行動を1つで決めつけないこと

まぁ…簡単じゃないけどね。
自分をすり減らす恋だけは、しなくていいと思うよ。
""".strip()

# =========================
# 人間寄せ微揺らし
# =========================

def human_like_jitter(text: str) -> str:
    lines = text.splitlines()
    out = []

    for line in lines:
        if random.random() < 0.08:
            line += random.choice(["。", "…", ""])
        if random.random() < 0.05:
            line = line.replace("です。", "です")
        if random.random() < 0.04:
            line = line.replace("ます。", "ます…")
        out.append(line)

    return "\n".join(out)

# =========================
# AI臭スコア
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

    noise = 10 if any(x in text for x in ["正直", "まぁ", "たぶん", "…"]) else 0

    return {"score": int(min(100, uniformity + phrase_score + repetition + noise))}

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
# メイン
# =========================

def main():
    safe_print("=== daily_update START ===")

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    pages = []

    # --- 毎日必ずN本生成 ---
    for i in range(DAILY_GENERATE_COUNT):
        fname = datetime.now().strftime("%Y%m%d") + f"_{i}.html"
        path = CONTENT_DIR / fname

        if path.exists():
            continue

        text = human_like_jitter(generate_python_article())
        path.write_text(text, encoding="utf-8")
        safe_print(f"[CREATE] {fname}")

    # --- 全記事処理 ---
    for file in CONTENT_DIR.glob("*.html"):
        try:
            text = human_like_jitter(file.read_text(encoding="utf-8"))
            score = mass_production_score(text)["score"]
            file.write_text(text, encoding="utf-8")

            loc = f"{SITE_URL}/content/{file.stem}"
            lastmod = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + TIMEZONE
            pages.append({"loc": loc, "lastmod": lastmod})

            safe_print(f"[OK] {file.name} | AI臭スコア={score}")

        except Exception:
            traceback.print_exc()
            continue

    generate_sitemap(pages)
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
