#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import traceback
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, ElementTree

# =========================
# Paths / Settings
# =========================

POST_DIR = Path("posts")
DATA_DIR = Path("data")
QUESTIONS_PATH = DATA_DIR / "questions.json"
TEMPLATE_PATH = Path("post_template.html")

PUBLIC_DIR = Path("public")
SITEMAP_PATH = PUBLIC_DIR / "sitemap.xml"

SITE_URL = "https://trend9.github.io/love-auto"
DAILY_GENERATE_COUNT = 2

LLAMA_BIN = "./llama.cpp/main"
LLAMA_MODEL = "./models/model.gguf"

# =========================
# Utils
# =========================

def safe_print(msg):
    try:
        print(msg, flush=True)
    except Exception:
        pass

def load_questions():
    if not QUESTIONS_PATH.exists():
        return []
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))

# =========================
# LLM
# =========================

def call_llm(prompt: str) -> dict:
    cmd = [
        LLAMA_BIN,
        "-m", LLAMA_MODEL,
        "-p", prompt,
        "--temp", "0.9",
        "--top-p", "0.95",
        "--n-predict", "2048"
    ]

    r = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=180
    )

    raw = r.stdout.strip()
    s = raw.find("{")
    e = raw.rfind("}")
    if s == -1 or e == -1:
        raise RuntimeError("LLM JSON parse error")

    return json.loads(raw[s:e+1])

# =========================
# Prompt
# =========================

def build_prompt(title, question):
    return f"""
あなたは日本の恋愛相談サイトの記事執筆者です。

【厳守】
・人間が書いた自然文体
・h1〜h3構成を前提に内容分割
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

def render_html(data, q, slug):
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)

    html = tpl
    html = html.replace("{{TITLE}}", data["title"])
    html = html.replace("{{META_DESCRIPTION}}", data["meta_description"])
    html = html.replace("{{LEAD}}", data["lead"])
    html = html.replace("{{QUESTION}}", q)
    html = html.replace("{{SUMMARY_ANSWER}}", data["summary_answer"])
    html = html.replace("{{PSYCHOLOGY}}", data["psychology"])
    html = html.replace("{{ACTION_LIST}}", "".join(f"<li>{x}</li>" for x in data["actions"]))
    html = html.replace("{{NG_LIST}}", "".join(f"<li>{x}</li>" for x in data["ng"]))
    html = html.replace("{{MISUNDERSTANDING}}", data["misunderstanding"])
    html = html.replace("{{CONCLUSION}}", data["conclusion"])
    html = html.replace("{{DATE_JP}}", now.astimezone().strftime("%Y年%m月%d日"))
    html = html.replace("{{DATE_ISO}}", now.isoformat())
    html = html.replace("{{PAGE_URL}}", f"{SITE_URL}/posts/{slug}.html")
    html = html.replace("{{CANONICAL}}", f'<link rel="canonical" href="{SITE_URL}/posts/{slug}.html">')
    html = html.replace("{{FAQ}}", "")
    html = html.replace("{{RELATED}}", "")
    html = html.replace("{{PREV}}", "")
    html = html.replace("{{NEXT}}", "")

    return html

# =========================
# Sitemap
# =========================

def generate_sitemap(pages):
    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for p in pages:
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = p["loc"]
        SubElement(url, "lastmod").text = p["lastmod"]

    PUBLIC_DIR.mkdir(exist_ok=True)
    ElementTree(urlset).write(SITEMAP_PATH, encoding="utf-8", xml_declaration=True)

# =========================
# Main
# =========================

def main():
    safe_print("=== daily_update START ===")

    POST_DIR.mkdir(exist_ok=True)
    questions = load_questions()[-DAILY_GENERATE_COUNT:]

    pages = []

    for q in questions:
        slug = q["slug"]
        path = POST_DIR / f"{slug}.html"
        if path.exists():
            continue

        prompt = build_prompt(q["title"], q["question"])
        data = call_llm(prompt)

        html = render_html(data, q["question"], slug)
        path.write_text(html, encoding="utf-8")

        pages.append({
            "loc": f"{SITE_URL}/posts/{slug}.html",
            "lastmod": datetime.now(timezone.utc).isoformat()
        })

        safe_print(f"[CREATE] {slug}.html")

    generate_sitemap(pages)
    safe_print("=== daily_update END ===")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
