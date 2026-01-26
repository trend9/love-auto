import json
import os
import re
from datetime import datetime
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POSTS_DIR = BASE_DIR / "posts"
TEMPLATE_PATH = BASE_DIR / "post_template.html"

QUESTIONS_PATH = DATA_DIR / "questions.json"
USED_PATH = DATA_DIR / "used_questions.json"

POSTS_DIR.mkdir(exist_ok=True)

def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def slugify(text):
    text = re.sub(r"[^\wぁ-んァ-ン一-龥ー]+", "", text)
    return text[:40]

def call_llm(prompt):
    proc = subprocess.run(
        ["./llama", "-p", prompt],
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()

def main():
    print("=== daily_update START ===")

    questions = load_json(QUESTIONS_PATH, [])
    used = load_json(USED_PATH, [])

    if not questions:
        print("No questions. Exit.")
        return

    # 最新1件のみ処理
    q = questions.pop(0)

    if not isinstance(q, dict) or "question" not in q:
        print("Invalid question format. Abort.")
        return

    question_text = q["question"]

    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    date_iso = today.isoformat()
    date_jp = today.strftime("%Y年%m月%d日")

    slug = slugify(question_text)
    filename = f"{date_str}-{slug}.html"
    post_path = POSTS_DIR / filename

    prompt = f"""
あなたは日本語専門の恋愛相談ライターです。

【絶対ルール】
・英語禁止
・翻訳文、Translation、英語要約を出力しない
・JSONのみ出力
・装飾不要
・自然で丁寧な日本語

【入力相談】
{question_text}

【出力JSON形式】
{{
  "title": "",
  "lead": "",
  "summary_answer": "",
  "psychology": "",
  "actions": ["", "", ""],
  "ng_actions": ["", ""],
  "misunderstanding": "",
  "conclusion": "",
  "meta_description": ""
}}
"""

    raw = call_llm(prompt)

    try:
        data = json.loads(raw)
    except Exception:
        print("Invalid LLM output. Abort.")
        return

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    html = template
    html = html.replace("{{TITLE}}", data["title"])
    html = html.replace("{{META_DESCRIPTION}}", data["meta_description"])
    html = html.replace("{{DATE_ISO}}", date_iso)
    html = html.replace("{{DATE_JP}}", date_jp)
    html = html.replace("{{LEAD}}", data["lead"])
    html = html.replace("{{QUESTION}}", question_text)
    html = html.replace("{{SUMMARY_ANSWER}}", data["summary_answer"])
    html = html.replace("{{PSYCHOLOGY}}", data["psychology"])
    html = html.replace(
        "{{ACTION_LIST}}",
        "\n".join(f"<li>{a}</li>" for a in data["actions"])
    )
    html = html.replace(
        "{{NG_LIST}}",
        "\n".join(f"<li>{a}</li>" for a in data["ng_actions"])
    )
    html = html.replace("{{MISUNDERSTANDING}}", data["misunderstanding"])
    html = html.replace("{{CONCLUSION}}", data["conclusion"])
    html = html.replace("{{FAQ}}", "")
    html = html.replace(
        "{{CANONICAL}}",
        f'<link rel="canonical" href="https://trend9.github.io/love-auto/posts/{filename}">'
    )
    html = html.replace(
        "{{PAGE_URL}}",
        f"https://trend9.github.io/love-auto/posts/{filename}"
    )
    html = html.replace("{{RELATED}}", "")
    html = html.replace("{{PREV}}", "")
    html = html.replace("{{NEXT}}", "")

    post_path.write_text(html, encoding="utf-8")

    used.append(q)
    save_json(USED_PATH, used)
    save_json(QUESTIONS_PATH, questions)

    print(f"✔ HTML generated: {filename}")
    print("=== daily_update END ===")

if __name__ == "__main__":
    main()
