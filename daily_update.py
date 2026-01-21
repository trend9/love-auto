import os, json, re
from datetime import datetime
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
THEME = "結婚の焦り"

ANSWER_MIN = 100
ANSWER_MAX = 200

# =====================
# Utils
# =====================

def clean(t):
    if not t:
        return ""
    return re.sub(r'[<>#*\[\]]', '', t).strip()

def extract(label, text):
    m = re.search(rf"{label}[：:]\s*(.*?)(?=\n\d\.|$)", text, re.S)
    return clean(m.group(1)) if m else ""

def normalize_answer(t):
    if len(t) > ANSWER_MAX:
        return t[:ANSWER_MAX].rstrip("。") + "。"
    if len(t) < ANSWER_MIN:
        return t + " 焦らず、自分の気持ちを大切にしてみてね。"
    return t

# =====================
# AI Generation
# =====================

def generate_article(llm, theme):
    prompt = f"""<|begin_of_text|>
<|start_header_id|>system<|end_header_id|>
あなたは35歳の日本人女性「ゆい姉さん」です。
恋愛相談に慣れていて、優しく現実的に答えます。
<|end_of_text|>

<|start_header_id|>user<|end_header_id|>
テーマ「{theme}」で恋愛相談記事を作ってください。
以下の形式を必ず守って日本語で書いてください。

1.ラジオネーム:
2.SEOタイトル:
3.相談文:
4.回答文:
5.メタディスクリプション:
<|end_of_text|>

<|start_header_id|>assistant<|end_header_id|>
"""

    out = llm(
        prompt,
        max_tokens=600,
        temperature=0.6,
        top_p=0.9,
        repeat_penalty=1.2,
        stop=["<|end_of_text|>"]
    )["choices"][0]["text"]

    print("====== RAW OUTPUT ======")
    print(out)
    print("========================")

    return {
        "radio": extract("1.ラジオネーム", out),
        "title": extract("2.SEOタイトル", out),
        "letter": extract("3.相談文", out),
        "answer": extract("4.回答文", out),
        "desc": extract("5.メタディスクリプション", out),
    }

# =====================
# Save files
# =====================

def save_article(data, template):
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    date = now.strftime("%Y/%m/%d %H:%M")

    html = (
        template
        .replace("{{SEO_TITLE}}", data["title"])
        .replace("{{SEO_DESCRIPTION}}", data["desc"])
        .replace("{{TITLE}}", f'{data["radio"]}さんからのお便り')
        .replace("{{LETTER}}", data["letter"])
        .replace("{{ANSWER}}", data["answer"])
        .replace("{{DATE}}", date)
    )

    path = f"posts/{stamp}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "title": data["title"],
        "url": path,
        "date": date,
        "description": data["desc"]
    }

# =====================
# Main
# =====================

def main():
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        verbose=True
    )

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    data = generate_article(llm, THEME)

    # 最低条件チェック
    if not data["title"] or not data["letter"] or not data["answer"]:
        raise RuntimeError("AI OUTPUT INVALID")

    data["answer"] = normalize_answer(data["answer"])

    item = save_article(data, template)

    # JSON 更新
    db = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except:
                pass

    db.insert(0, item)

    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print("SUCCESSFULLY GENERATED")

if __name__ == "__main__":
    main()
