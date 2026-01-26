import json
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
# JSON Utility
# =========================
def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# used_questions 安全取得
# =========================
questions = load_json(QUESTIONS_PATH, [])

if not questions:
    raise RuntimeError("used_questions.json が空です")

latest = questions[-1]

if isinstance(latest, str):
    question_text = latest
elif isinstance(latest, dict):
    question_text = (
        latest.get("question")
        or latest.get("text")
        or latest.get("content")
    )
else:
    raise RuntimeError("used_questions.json の形式が不正です")

if not question_text:
    raise RuntimeError("質問文が取得できません")

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

【必須】
・全て日本語
・出力形式を厳守
・各項目は必ず1文以上

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
# LLM 実行
# =========================
res = llm(
    PROMPT + question_text,
    max_tokens=1600,
)

output = res["choices"][0]["text"].strip()

required = [
    "タイトル：",
    "要約：",
    "結論：",
    "相手の心理：",
    "具体的な行動：",
    "避けたい行動：",
    "よくある勘違い：",
    "まとめ：",
]

if not all(k in output for k in required):
    raise RuntimeError("Invalid LLM output")

# =========================
# 抽出関数
# =========================
def extract_block(key):
    m = re.search(rf"{key}：(.+?)(?=\n\S+：|\Z)", output, re.S)
    return m.group(1).strip() if m else ""


def extract_list(key):
    block = extract_block(key)
    return [
        line[1:].strip()
        for line in block.splitlines()
        if line.strip().startswith("-")
    ]


title = extract_block("タイトル")
summary = extract_block("要約")
conclusion = extract_block("結論")
psychology = extract_block("相手の心理")
actions = extract_list("具体的な行動")
ng_actions = extract_list("避けたい行動")
misunderstanding = extract_block("よくある勘違い")
closing = extract_block("まとめ")

# =========================
# HTML生成
# =========================
slug = datetime.now().strftime("%Y%m%d")
post_path = POSTS_DIR / f"{slug}.html"

with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
    template = f.read()

html = template
html = html.replace("{{TITLE}}", title)
html = html.replace("{{META_DESCRIPTION}}", summary)
html = html.replace("{{LEAD}}", summary)
html = html.replace("{{QUESTION}}", question_text)
html = html.replace("{{SUMMARY_ANSWER}}", conclusion)
html = html.replace("{{PSYCHOLOGY}}", psychology)
html = html.replace(
    "{{ACTION_LIST}}",
    "\n".join(f"<li>{a}</li>" for a in actions),
)
html = html.replace(
    "{{NG_LIST}}",
    "\n".join(f"<li>{a}</li>" for a in ng_actions),
)
html = html.replace("{{MISUNDERSTANDING}}", misunderstanding)
html = html.replace("{{CONCLUSION}}", closing)
html = html.replace("{{DATE_JP}}", datetime.now().strftime("%Y年%m月%d日"))
html = html.replace("{{DATE_ISO}}", datetime.now().strftime("%Y-%m-%d"))
html = html.replace("{{PAGE_URL}}", f"https://trend9.github.io/love-auto/posts/{slug}.html")
html = html.replace("{{CANONICAL}}", f'<link rel="canonical" href="https://trend9.github.io/love-auto/posts/{slug}.html">')
html = html.replace("{{FAQ}}", "")
html = html.replace("{{RELATED}}", "")
html = html.replace("{{PREV}}", "")
html = html.replace("{{NEXT}}", "")

with open(post_path, "w", encoding="utf-8") as f:
    f.write(html)

# =========================
# index.json 更新
# =========================
index = load_json(INDEX_PATH, [])
index.insert(0, {
    "title": title,
    "summary": summary,
    "url": f"posts/{slug}.html",
    "date": datetime.now().strftime("%Y-%m-%d"),
})

save_json(INDEX_PATH, index)

print("=== daily_update END ===")
