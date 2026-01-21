import os
import json
import random
from datetime import datetime
from llama_cpp import Llama

# =========================
# 設定
# =========================

MODEL_PATH = "./models/model.gguf"
POSTS_DIR = "posts"
DATA_DIR = "data"
QUESTIONS_JSON = os.path.join(DATA_DIR, "questions.json")
POST_TEMPLATE = "post_template.html"

MAX_RETRY = 3

# =========================
# ユーティリティ
# =========================

def now():
    return datetime.now()

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_text(text: str) -> str:
    """
    LLM事故防止用クリーナー
    """
    banned = [
        "Here is", "Please write", "回答例", "出題", "```", "python",
        "【", "】", "(回答", "(例)", "Title:", "Meta"
    ]
    for b in banned:
        text = text.replace(b, "")
    return text.strip()

# =========================
# LLM 初期化
# =========================

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    temperature=0.7,
    top_p=0.9,
    repeat_penalty=1.1,
)

def generate(prompt: str) -> str:
    res = llm(
        prompt,
        max_tokens=512,
        stop=["<|endoftext|>"]
    )
    return clean_text(res["choices"][0]["text"])

# =========================
# 生成ロジック
# =========================

def generate_theme():
    prompt = """
あなたは恋愛相談ラジオの編集者です。
以下の条件を必ず守ってください。

【条件】
・日本語のみ
・1行のみ
・説明や前置きは禁止
・テーマ文だけを出力

【出力例】
結婚の焦りに悩む30代女性の恋愛相談
"""
    return generate(prompt)

def generate_radio_name():
    prompt = """
日本人女性のラジオネームを1つだけ出力してください。

【条件】
・ひらがな or カタカナ
・2〜4文字
・名前のみ
"""
    return generate(prompt)

def generate_letter(theme, name):
    prompt = f"""
あなたは恋愛相談番組に投稿する一般女性です。

【条件】
・日本語のみ
・説明禁止
・400〜600文字
・情景が浮かぶ具体的な悩み
・一人称は「私」

【テーマ】
{theme}

【ラジオネーム】
{name}
"""
    return generate(prompt)

def generate_answer(letter, name):
    prompt = f"""
あなたは恋愛相談ラジオの回答者「結姉さん」です。

【構成（厳守）】
1. 共感（2〜3文）
2. 悩みの核心（1〜2文）
3. 視点の整理・提案（3〜4文）
4. 優しい一言で締め

【条件】
・日本語のみ
・説教禁止
・箇条書き禁止
・コード・英語禁止

【相談文】
{letter}
"""
    return generate(prompt)

def generate_meta(theme, letter):
    prompt = f"""
以下の内容を要約し、検索結果用のメタディスクリプションを書いてください。

【条件】
・日本語のみ
・100〜120文字
・説明文や前置き禁止
・1文のみ

【テーマ】
{theme}

【本文】
{letter}
"""
    return generate(prompt)

# =========================
# HTML生成
# =========================

def render_html(template, data):
    html = template
    for k, v in data.items():
        html = html.replace(f"{{{{{k}}}}}", v)
    return html

# =========================
# メイン処理
# =========================

def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    questions = load_json(QUESTIONS_JSON, [])

    for _ in range(MAX_RETRY):
        try:
            theme = generate_theme()
            name = generate_radio_name()
            letter = generate_letter(theme, name)
            answer = generate_answer(letter, name)
            meta = generate_meta(theme, letter)

            if not all([theme, name, letter, answer, meta]):
                raise ValueError("生成失敗")

            break
        except Exception:
            continue
    else:
        raise RuntimeError("AI生成失敗")

    dt = now()
    date_str = dt.strftime("%Y/%m/%d %H:%M")
    file_id = dt.strftime("%Y%m%d_%H%M%S")
    filename = f"{file_id}.html"
    filepath = os.path.join(POSTS_DIR, filename)

    with open(POST_TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    html = render_html(template, {
        "TITLE": theme,
        "META": meta,
        "DATE": date_str,
        "NAME": name,
        "LETTER": letter,
        "ANSWER": answer,
    })

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    questions.insert(0, {
        "title": theme,
        "url": f"posts/{filename}",
        "date": date_str,
        "description": meta
    })

    save_json(QUESTIONS_JSON, questions)

    print("OK: article generated")

if __name__ == "__main__":
    main()
