import os, json, re, random
from datetime import datetime
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 5
MAX_RETRY = 3

ANSWER_MIN = 100
ANSWER_MAX = 200

# -------------------------
# Utility
# -------------------------

def clean(text):
    if not text:
        return ""
    text = re.sub(r'[<>#*\[\]]', '', text)
    return text.strip()

def extract(label, text):
    m = re.search(rf"{label}[：:]\s*(.*?)(?=\n\d\.|$)", text, re.S)
    return clean(m.group(1)) if m else ""

def char_len(text):
    return len(text)

# -------------------------
# Theme Generation
# -------------------------

def load_recent_themes(limit=20):
    path = "data/questions.json"
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            return []
    return [q["title"] for q in data[:limit]]

def generate_themes(llm, avoid_titles, count):
    avoid_text = " / ".join(avoid_titles[:10])

    prompt = f"""System:
あなたは恋愛相談サイトの編集者です。

User:
以下は最近使われた記事タイトルです。
これらと被らない「恋愛相談テーマ」を {count} 個考えてください。

最近のタイトル:
{avoid_text}

条件:
・短い名詞句
・日本語
・重複禁止
・番号付きで出力

Assistant:
"""

    out = llm(
        prompt,
        max_tokens=200,
        temperature=0.6,
        repeat_penalty=1.1,
        stop=["6."]
    )["choices"][0]["text"]

    themes = re.findall(r'\d+\.\s*(.+)', out)
    return themes[:count]

# -------------------------
# AI Article Generation
# -------------------------

def generate_article(llm, theme):
    prompt = f"""System:
あなたは35歳の日本人女性「ゆい姉さん」です。
恋愛相談に慣れており、優しく現実的に答えます。

User:
以下のテーマで恋愛相談記事を作ってください。
テーマ: {theme}

形式を必ず守ってください。

1.ラジオネーム:
2.SEOタイトル:
3.相談文:
4.回答文:
5.メタディスクリプション:

Assistant:
"""

    out = llm(
        prompt,
        max_tokens=400,
        temperature=0.5,
        top_p=0.9,
        repeat_penalty=1.15,
        stop=["6."]
    )["choices"][0]["text"]

    data = {
        "radio_name": extract("1.ラジオネーム", out),
        "seo_title": extract("2.SEOタイトル", out),
        "letter": extract("3.相談文", out),
        "answer": extract("4.回答文", out),
        "description": extract("5.メタディスクリプション", out),
    }

    return data

def validate_article(data):
    if len(data["seo_title"]) < 8:
        return False
    if len(data["letter"]) < 50:
        return False
    alen = char_len(data["answer"])
    if alen < ANSWER_MIN or alen > ANSWER_MAX:
        return False
    return True

# -------------------------
# Save & Update
# -------------------------

def save_article(data, template):
    os.makedirs("posts", exist_ok=True)
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    display_date = now.strftime("%Y/%m/%d %H:%M")
    filename = f"posts/{stamp}.html"

    html = (
        template
        .replace("{{SEO_TITLE}}", data["seo_title"])
        .replace("{{SEO_DESCRIPTION}}", data["description"][:100])
        .replace("{{TITLE}}", f'{data["radio_name"]}さんからのお便り')
        .replace("{{LETTER}}", data["letter"])
        .replace("{{ANSWER}}", data["answer"])
        .replace("{{DATE}}", display_date)
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "title": data["seo_title"],
        "url": filename,
        "date": display_date,
        "description": data["description"]
    }

def update_json(new_items):
    os.makedirs("data", exist_ok=True)
    path = "data/questions.json"
    db = []

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except:
                pass

    db = new_items + db
    db = db[:1000]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    return db

def update_index(db):
    if not os.path.exists("index.html"):
        return

    items = ""
    for q in db[:5]:
        items += f'<li><a href="{q["url"]}">{q["title"]}</a><span>{q["date"]}</span></li>\n'

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(
        r'<!-- LATEST_START -->.*?<!-- LATEST_END -->',
        f'<!-- LATEST_START -->\n<ul>\n{items}</ul>\n<!-- LATEST_END -->',
        html,
        flags=re.S
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def update_archive(db):
    if not os.path.exists("archive.html"):
        return

    rows = ""
    for q in db:
        rows += f'<li><a href="{q["url"]}">{q["title"]}</a><span>{q["date"]}</span></li>\n'

    with open("archive.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = re.sub(
        r'<!-- ARCHIVE_START -->.*?<!-- ARCHIVE_END -->',
        f'<!-- ARCHIVE_START -->\n<ul>\n{rows}</ul>\n<!-- ARCHIVE_END -->',
        html,
        flags=re.S
    )

    with open("archive.html", "w", encoding="utf-8") as f:
        f.write(html)

# -------------------------
# Main
# -------------------------

def main():
    if not os.path.exists(MODEL_PATH):
        return

    llm = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False)

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    recent_titles = load_recent_themes()
    themes = generate_themes(llm, recent_titles, GENERATE_COUNT)

    new_items = []

    for theme in themes:
        for _ in range(MAX_RETRY):
            data = generate_article(llm, theme)
            if validate_article(data):
                item = save_article(data, template)
                new_items.append(item)
                break

    if new_items:
        db = update_json(new_items)
        update_index(db)
        update_archive(db)

if __name__ == "__main__":
    main()
