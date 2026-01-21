import os, json, re
from datetime import datetime
from llama_cpp import Llama

# =====================
# CONFIG
# =====================
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 5
MAX_RETRY = 3

ANSWER_MIN = 100
ANSWER_MAX = 200

# =====================
# UTILS
# =====================

def clean(text):
    if not text:
        return ""
    return re.sub(r'[<>#*\[\]]', '', text).strip()

def extract(label, text):
    m = re.search(rf"{label}[：:]\s*(.*?)(?=\n\d\.|$)", text, re.S)
    return clean(m.group(1)) if m else ""

def normalize_answer(text):
    if len(text) > ANSWER_MAX:
        return text[:ANSWER_MAX].rstrip("。") + "。"
    if len(text) < ANSWER_MIN:
        return text + " 焦らず、自分の気持ちを大切にしてみてね。"
    return text

# =====================
# LOAD PAST DATA
# =====================

def load_recent_titles(limit=20):
    path = "data/questions.json"
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return [q["title"] for q in data[:limit]]
        except:
            return []

# =====================
# THEME GENERATION
# =====================

def generate_themes(llm, avoid_titles, count):
    avoid = " / ".join(avoid_titles[:10])

    prompt = f"""System:
あなたは恋愛相談サイトの編集者です。

User:
以下は最近使われた記事タイトルです。
これらと被らない「恋愛相談テーマ」を {count} 個考えてください。

最近のタイトル:
{avoid}

条件:
・短い日本語
・重複しない
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

# =====================
# ARTICLE GENERATION
# =====================

def generate_article(llm, theme):
    prompt = f"""System:
あなたは35歳の日本人女性「ゆい姉さん」です。
恋愛相談に慣れていて、優しく現実的に答えます。

User:
以下のテーマで恋愛相談記事を作ってください。
テーマ: {theme}

必ず次の形式で出力してください。

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

    return {
        "radio_name": extract("1.ラジオネーム", out),
        "seo_title": extract("2.SEOタイトル", out),
        "letter": extract("3.相談文", out),
        "answer": extract("4.回答文", out),
        "description": extract("5.メタディスクリプション", out),
    }

def validate_article(data):
    if not data["seo_title"]:
        return False
    if len(data["letter"]) < 30:
        return False
    if len(data["answer"]) < 80:
        return False
    return True

# =====================
# SAVE / UPDATE FILES
# =====================

def save_article(data, template):
    os.makedirs("posts", exist_ok=True)

    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    display_date = now.strftime("%Y/%m/%d %H:%M")
    path = f"posts/{stamp}.html"

    html = (
        template
        .replace("{{SEO_TITLE}}", data["seo_title"])
        .replace("{{SEO_DESCRIPTION}}", data["description"][:100])
        .replace("{{TITLE}}", f'{data["radio_name"]}さんからのお便り')
        .replace("{{LETTER}}", data["letter"])
        .replace("{{ANSWER}}", data["answer"])
        .replace("{{DATE}}", display_date)
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "title": data["seo_title"],
        "url": path,
        "date": display_date,
        "description": data["description"]
    }

def update_json(items):
    os.makedirs("data", exist_ok=True)
    path = "data/questions.json"
    db = []

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except:
                pass

    db = items + db
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

# =====================
# MAIN
# =====================

def main():
    if not os.path.exists(MODEL_PATH):
        print("MODEL NOT FOUND")
        return

    llm = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False)

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    recent_titles = load_recent_titles()
    themes = generate_themes(llm, recent_titles, GENERATE_COUNT)

    new_items = []

    for theme in themes:
        for _ in range(MAX_RETRY):
            data = generate_article(llm, theme)
            if validate_article(data):
                data["answer"] = normalize_answer(data["answer"])
                item = save_article(data, template)
                new_items.append(item)
                break

    # 最低1件は必ず出す保険
    if not new_items:
        data = generate_article(llm, themes[0])
        data["answer"] = normalize_answer(data["answer"])
        item = save_article(data, template)
        new_items.append(item)

    db = update_json(new_items)
    update_index(db)
    update_archive(db)

if __name__ == "__main__":
    main()
