import json
import os
import re
from datetime import datetime
from pathlib import Path

from llama_cpp import Llama


print("=== daily_update START ===")

# =========================
# パス定義
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POSTS_DIR = BASE_DIR / "posts"
TEMPLATE_PATH = BASE_DIR / "post_template.html"

QUESTIONS_PATH = DATA_DIR / "used_questions.json"
INDEX_PATH = BASE_DIR / "index.json"

POSTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# =========================
# LLM 初期化
# =========================
llm = Llama(
    model_path="./models/model.gguf",
    n_ctx=2048,
    n_threads=4,
    verbose=False,
)

PROMPT = """
以下の恋愛相談に対して、日本語のみで恋愛相談記事を書いてください。
英語・ローマ字・翻訳文は禁止です。

【必須条件】
・全て日本語
・SEOを意識した丁寧な文章
・各項目は必ず1文以上書く
・出力形式を厳守する

【出力フォーマット】
タイトル：
要約：
結論：
相手の心理：
具体的な行動：
- 行動1
- 行動2
- 行動3
避けたい行動：
- NG行動1
- NG行動2
よくある勘違い：
まとめ：

【相談内容】
"""


# =========================
# ユーティリティ
# =========================
def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_section(text, key):
    pattern = rf"{key}：(.+?)(?=\n\S+：|\Z)"
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else ""


def extract_list(text, key):
    block = extract_section(text, key)
    items = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("-"):
            items.append(line[1:].strip())
    return items


# =========================
# データ読み込み
# =========================
questions = load_json(QUESTIONS_PATH, [])
if not questions:
    raise RuntimeError("used_questions.json が空です")

question = questions[-1]["question"]

index = load_json(INDEX_PATH, [])


# =========================
# LLM 実行
# =========================
res = llm(
    PROMPT + question,
    max_tokens=1600,
)

output = res["choices"][0]["text"].strip()

required_keys = [
    "タイトル",
    "要約",
    "結論",
    "相手の心理",
    "具体的な行動",
    "避けたい行動",
    "よくある勘違い",
    "まとめ",
]

if not all(k + "：" in output for k in required_keys):
    raise RuntimeError("Invalid LLM output")


# =========================
# 各要素抽出
# =========================
title = extract_section(output, "タイトル")
summary = extract_section(output, "要約")
conclusion = extract_section(output, "結論")
psychology = extract_section(output, "相手の心理")
actions = extract_list(output, "具体的な行動")
ng_actions = extract_list(output, "避けたい行動")
misunderstanding = extract_section(output, "よくある勘違い")
closing = extract_section(output, "まとめ")

slug = datetime.now().strftime("%Y%m%d")
post_path = POSTS_DIR / f"{slug}.html"


# =========================
# HTML生成
# =========================
with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = f.read()

html = template
html = html.replace("{{TITLE}}", title)
html = html.replace("{{SUMMARY}}", summary)
html = html.replace("{{CONCLUSION}}", conclusion)
html = html.replace("{{PSYCHOLOGY}}", psychology)
html = html.replace(
    "{{ACTIONS}}",
    "\n".join(f"<li>{a}</li>" for a in actions),
)
html = html.replace(
    "{{NG_ACTIONS}}",
    "\n".join(f"<li>{a}</li>" for a in ng_actions),
)
html = html.replace("{{MISUNDERSTANDING}}", misunderstanding)
html = html.replace("{{CLOSING}}", closing)
html = html.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)


# =========================
# index.json 更新
# =========================
index.insert(
    0,
    {
        "title": title,
        "summary": summary,
        "slug": slug,
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
)

save_json(INDEX_PATH, index)

print("=== daily_update END ===")
