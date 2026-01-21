import os, json, re, time, random
from datetime import datetime
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
POST_DIR = "posts"
DATA_DIR = "data"
JSON_PATH = "data/questions.json"
ARCHIVE_PATH = "archive.html"

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =====================
# AI 初期化
# =====================
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4,
    temperature=0.7,
)

# =====================
# テーマ被り防止
# =====================
used_themes = []
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        used_themes = [q["title"] for q in json.load(f)]

themes = [
    "結婚の焦り",
    "年齢と恋愛の不安",
    "周囲と比べてしまう恋",
    "将来が見えない恋人",
    "一人で生きる覚悟"
]

theme = random.choice([t for t in themes if t not in used_themes] or themes)

# =====================
# プロンプト（超重要）
# =====================
PROMPT = f"""
あなたは35歳の女性「結姉さん」です。
必ず以下の形式のみで日本語出力してください。
英語・署名・説明は禁止。

1.ラジオネーム：
2.お便り内容：
3.結姉さんの回答：

【テーマ】
{theme}
"""

# =====================
# extract（ゆるい）
# =====================
def extract(label, text):
    m = re.search(rf"{label}[:：]\s*(.*?)(?=\n\d\.|$)", text, re.S)
    return m.group(1).strip() if m else ""

# =====================
# AI生成（リトライ付き）
# =====================
for _ in range(3):
    out = llm(PROMPT, max_tokens=800)["choices"][0]["text"]

    name = extract("1.ラジオネーム", out)
    letter = extract("2.お便り内容", out)
    answer = extract("3.結姉さんの回答", out)

    if name and letter and answer:
        break
else:
    raise RuntimeError("AI生成に失敗")

# =====================
# 日付生成
# =====================
now = datetime.now()
slug = now.strftime("%Y%m%d_%H%M%S")
url = f"posts/{slug}.html"
date_str = now.strftime("%Y/%m/%d %H:%M")

# =====================
# HTML生成
# =====================
with open("post_template.html", "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("{{TITLE}}", theme)
html = html.replace("{{DATE}}", date_str)
html = html.replace("{{NAME}}", name)
html = html.replace("{{LETTER}}", letter)
html = html.replace("{{ANSWER}}", answer)

with open(url, "w", encoding="utf-8") as f:
    f.write(html)

# =====================
# JSON更新
# =====================
entry = {
    "title": theme,
    "url": url,
    "date": date_str,
    "description": letter[:100]
}

data = []
if os.path.exists(JSON_PATH):
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

data.insert(0, entry)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# archive.html 自動生成（★必須）
# =====================
rows = ""
for q in data:
    rows += f'<li><a href="{q["url"]}">{q["title"]}</a> <span>{q["date"]}</span></li>\n'

archive_html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>相談アーカイブ</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h1>恋愛相談アーカイブ</h1>
<ul>
{rows}
</ul>
<a href="index.html">← トップへ</a>
</body>
</html>
"""

with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
    f.write(archive_html)
