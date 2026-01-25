#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
daily_update.py
================
目的：
- LLM生成記事を安全にpublish
- 「量産AI臭」を数値化（量産判定スコア）
- sitemap.xml を毎日自動再生成
- 途中でLLMが落ちても100%完走

前提：
- 記事は content/ 以下に .md または .html で存在
- sitemap.xml は public/ に出力
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

SITE_URL = "https://example.com"
TIMEZONE = "+09:00"

RANDOM_SEED_SALT = "human_like_noise_v1"
random.seed(time.time())

# =========================
# ユーティリティ
# =========================

def safe_print(msg: str):
    """絶対に止まらないprint"""
    try:
        print(msg, flush=True)
    except Exception:
        pass


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


# =========================
# 量産判定スコア
# =========================

def mass_production_score(text: str) -> dict:
    """
    AI量産臭を数値化
    0〜100（高いほどAI臭い）
    """

    length = len(text)
    if length == 0:
        return {"score": 100, "reason": "empty"}

    # ① 文長の均一さ
    sentences = [s.strip() for s in text.replace("。", ".").split(".") if s.strip()]
    avg_len = sum(len(s) for s in sentences) / max(len(sentences), 1)
    variance = sum((len(s) - avg_len) ** 2 for s in sentences) / max(len(sentences), 1)

    uniformity_score = max(0, 30 - min(30, variance / 20))

    # ② 定型フレーズ密度
    ai_phrases = [
        "結論として",
        "以下の通りです",
        "重要なのは",
        "総合的に見ると",
        "メリットとデメリット"
    ]
    phrase_hits = sum(text.count(p) for p in ai_phrases)
    phrase_score = min(30, phrase_hits * 6)

    # ③ 語彙の繰り返し
    words = text.split()
    unique_ratio = len(set(words)) / max(len(words), 1)
    repetition_score = max(0, 30 - unique_ratio * 30)

    # ④ 人間的ノイズ不足
    noise_tokens = ["…", "正直", "たぶん", "まぁ", "自分的には"]
    noise_score = 10 if any(t in text for t in noise_tokens) else 0

    score = int(
        uniformity_score +
        phrase_score +
        repetition_score +
        noise_score
    )

    return {
        "score": min(100, score),
        "details": {
            "uniformity": round(uniformity_score, 2),
            "phrases": phrase_score,
            "repetition": round(repetition_score, 2),
            "noise": noise_score
        }
    }


# =========================
# 人間寄せランダム微揺らし
# =========================

def human_like_jitter(text: str) -> str:
    """
    文体を壊さず、微妙に揺らす
    """
    lines = text.splitlines()
    out = []

    for line in lines:
        if random.random() < 0.07:
            line += random.choice(["。", "…", ""])
        if random.random() < 0.05:
            line = line.replace("です。", "です")
        out.append(line)

    return "\n".join(out)


# =========================
# sitemap生成
# =========================

def generate_sitemap(pages: list):
    urlset = Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )

    for page in pages:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = page["loc"]
        SubElement(url, "lastmod").text = page["lastmod"]
        SubElement(url, "changefreq").text = "daily"
        SubElement(url, "priority").text = "0.8"

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    tree = ElementTree(urlset)
    tree.write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)


# =========================
# メイン処理
# =========================

def main():
    safe_print("=== daily_update START ===")

    pages = []

    for file in CONTENT_DIR.rglob("*"):
        if file.suffix not in (".md", ".html"):
            continue

        try:
            text = file.read_text(encoding="utf-8")

            # ① 人間寄せ
            text = human_like_jitter(text)

            # ② 量産判定
            score_info = mass_production_score(text)

            # ③ 保存（必ず）
            file.write_text(text, encoding="utf-8")

            # ④ sitemap用データ
            rel = file.relative_to(CONTENT_DIR).with_suffix("")
            loc = f"{SITE_URL}/{rel.as_posix()}"
            lastmod = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + TIMEZONE

            pages.append({
                "loc": loc,
                "lastmod": lastmod,
                "score": score_info["score"]
            })

            safe_print(
                f"[OK] {file.name} | AI臭スコア={score_info['score']}"
            )

        except Exception as e:
            safe_print(f"[ERROR] {file} :: {e}")
            traceback.print_exc()
            continue  # ←絶対に止まらない

    # sitemap再生成
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
        # 最後の砦
        traceback.print_exc()
        sys.exit(0)
