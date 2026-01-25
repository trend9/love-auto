#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback
import json
from pathlib import Path
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree

from llama_cpp import Llama
from question_generator import generate_questions

# =========================
# Paths / Settings
# =========================

POST_DIR = Path("posts")
TEMPLATE_PATH = Path("post_template.html")

PUBLIC_DIR = Path("public")
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"

SITE_URL = "https://trend9.github.io/love-auto"

DAILY_GENERATE_COUNT = 2
MODEL_PATH = "./models/model.gguf"

# =========================
# Utils
# =========================

def safe_print(msg):
    try:
        print(msg, flush=True)
    except Exception:
        pass

# =========================
# LLM（記事生成）
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.9,
    top_p=0.95,
    repeat_penalty=1.1,
    verbose=False,
)

def call_llm(prompt: str) -> dict:
    r = llm(prompt, max_tokens=2048)
    text = r["choices"][0]["text"].strip()

    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1:
        raise RuntimeError("LLM JSON parse error")

    return json.loads(text[s:e+1])

# =========================
# Prompt
# =========================

def build_prompt(question):
    return f"""
あなたは日本の恋愛相談サイトの記事執筆者です。

【厳守】
・人間が書いた自然文体
・h1〜h3構成
・テンプレ感・一般論禁止
・JSONのみ出力

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
# HTML
# =========================

def render_html(data, question, slug):
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)

    html = tpl
    html = html.replace("{{TITLE}}", data["title"])
    html = html.replace("{{META_DESCRIPTION}}", data["meta_description"])
    html = html.replace("{{LEAD}}", data["lead"])
    html = html.replace("{{QUESTION}}", question)
    html = html.replace("{{SUMMARY_ANSWER}}", data["summary_answer"])
    html = html.replace("{{PSYCHOLOGY}}", data["psychology"])
    html = html.replace("{{ACTION_LIST}}", "".join(f"<li>{x}</li>" for x in data["actions"]))
    html = html.replace("{{NG_LIST}}", "".join(f"<li>{x}</li>" for x in data["ng"]))
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

    for html in POST_DIR.glob("*.html"):
        slug = html.stem
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = f"{SITE_URL}/posts/{slug}.html"
        SubElement(url, "lastmod").text = datetime.now(timezone.utc).isoformat()

    PUBLIC_DIR.mkdir(exist_ok=True)
    ElementTree(urlset).write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)

# =========================
# Main
# =========================

def main():
    safe_print("=== daily_update START ===")

    POST_DIR.mkdir(exist_ok=True)

    questions = generate_questions()
    targets = questions[:DAILY_GENERATE_COUNT]

    for q in targets:
        slug = q["slug"]
        path = POST_DIR / f"{slug}.html"

        if path.exists():
            safe_print(f"[SKIP] {slug}.html")
            continue

        prompt = build_prompt(q["question"])
        data = call_llm(prompt)

        html = render_html(data, q["question"], slug)
        path.write_text(html, encoding="utf-8")

        safe_print(f"[CREATE] {slug}.html")

    generate_sitemap()
    safe_print("=== daily_update END ===")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
