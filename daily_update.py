#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
import json
import random
from pathlib import Path
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree

from llama_cpp import Llama
from question_generator import generate_questions

# =========================
# Paths / Settings
# =========================

BASE_DIR = Path(__file__).parent

POST_DIR = BASE_DIR / "posts"
TEMPLATE_PATH = BASE_DIR / "post_template.html"

PUBLIC_DIR = BASE_DIR / "public"
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"

SITE_URL = "https://trend9.github.io/love-auto"

# cron前提：少量・確実
DAILY_GENERATE_COUNT = 1

MODEL_PATH = BASE_DIR / "models" / "model.gguf"

# =========================
# Utils
# =========================

def safe_print(msg: str):
    try:
        print(msg, flush=True)
    except Exception:
        pass

# =========================
# LLM 初期化
# =========================

safe_print("Initializing LLM...")

llm = Llama(
    model_path=str(MODEL_PATH),
    n_ctx=2048,
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.1,
    verbose=False,
)

# =========================
# LLM Call（JSON耐性MAX）
# =========================

def call_llm(prompt: str) -> dict | None:
    """
    ・壊れたJSONは例外を投げず None
    ・```json ``` や前後のゴミを除去
    ・cronを絶対に止めない
    """
    try:
        r = llm(prompt, max_tokens=2048)
        raw = r["choices"][0]["text"].strip()

        # コードフェンス除去
        raw = raw.replace("```json", "").replace("```", "").strip()

        s = raw.find("{")
        e = raw.rfind("}")

        if s == -1 or e == -1 or e <= s:
            return None

        return json.loads(raw[s:e + 1])

    except Exception:
        return None

# =========================
# Prompt
# =========================

def build_prompt(question: str) -> str:
    return f"""
あなたは日本の恋愛相談サイトの専属ライターです。

【厳守ルール】
・SEOを意識しすぎた不自然な文章は禁止
・人間が本音で書いたような自然文体
・一般論・テンプレ回答は禁止
・h1〜h3構成を意識
・JSON以外は絶対に出力しない

出力形式：
{{
  "title": "",
  "meta_description": "",
  "lead": "",
  "summary_answer": "",
  "psychology": "",
  "actions": ["", "", ""],
  "ng": ["", "", ""],
  "misunderstanding": "",
  "conclusion": ""
}}

相談内容：
{question}
""".strip()

# =========================
# HTML Render
# =========================

def render_html(data: dict, question: str, slug: str) -> str:
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)

    html = tpl
    html = html.replace("{{TITLE}}", data["title"])
    html = html.replace("{{META_DESCRIPTION}}", data["meta_description"])
    html = html.replace("{{LEAD}}", data["lead"])
    html = html.replace("{{QUESTION}}", question)
    html = html.replace("{{SUMMARY_ANSWER}}", data["summary_answer"])
    html = html.replace("{{PSYCHOLOGY}}", data["psychology"])
    html = html.replace(
        "{{ACTION_LIST}}",
        "".join(f"<li>{x}</li>" for x in data["actions"])
    )
    html = html.replace(
        "{{NG_LIST}}",
        "".join(f"<li>{x}</li>" for x in data["ng"])
    )
    html = html.replace("{{MISUNDERSTANDING}}", data["misunderstanding"])
    html = html.replace("{{CONCLUSION}}", data["conclusion"])
    html = html.replace("{{DATE_JP}}", now.astimezone().strftime("%Y年%m月%d日"))
    html = html.replace("{{DATE_ISO}}", now.isoformat())
    html = html.replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{slug}.html")
    html = html.replace(
        "{{CANONICAL}}",
        f'<link rel="canonical" href="{SITE_URL}/posts/{slug}.html">'
    )

    return html

# =========================
# Sitemap
# =========================

def generate_sitemap():
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    for html_file in sorted(POST_DIR.glob("*.html")):
        slug = html_file.stem
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{SITE_URL}/posts/{slug}.html"
        SubElement(url, "lastmod").text = datetime.now(timezone.utc).isoformat()

    PUBLIC_DIR.mkdir(exist_ok=True)
    ElementTree(urlset).write(
        SITEMAP_PATH,
        encoding="utf-8",
        xml_declaration=True
    )

# =========================
# Main
# =========================

def main():
    safe_print("=== daily_update START ===")

    POST_DIR.mkdir(exist_ok=True)

    questions = generate_questions()
    if not questions:
        safe_print("No questions generated")
        return

    targets = random.sample(
        questions,
        k=min(DAILY_GENERATE_COUNT, len(questions))
    )

    for q in targets:
        slug = q["slug"]
        path = POST_DIR / f"{slug}.html"

        if path.exists():
            safe_print(f"[SKIP] {slug}.html already exists")
            continue

        safe_print(f"[GEN] {slug}")

        prompt = build_prompt(q["question"])
        data = call_llm(prompt)

        if not data:
            safe_print(f"[SKIP] JSON parse failed: {slug}")
            continue

        html = render_html(data, q["question"], slug)
        path.write_text(html, encoding="utf-8")

        safe_print(f"[CREATE] {slug}.html")

    generate_sitemap()
    safe_print("=== daily_update END ===")

# =========================
# Entrypoint
# =========================

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
