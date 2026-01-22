import json
import os
from datetime import datetime
from llama_cpp import Llama

# =========================
# 設定
# =========================

MODEL_PATH = "./models/model.gguf"

QUESTIONS_FILE = "data/questions.json"
USED_QUESTIONS_FILE = "data/used_questions.json"

GENERATE_COUNT = 5
MAX_TOKENS = 512
TEMPERATURE = 0.8

# =========================
# 安全チェック
# =========================

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        f"❌ LLMモデルが見つかりません: {MODEL_PATH}\n"
        f"GitHub Actionsでは model をDLしています。\n"
        f"ローカルで実行する場合は models/model.gguf を配置してください。"
    )

# =========================
# LLM 初期化（完全ローカル）
# =========================

llm = Llama(
    model_path="./models/model.gguf",
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=0,   # ← ここ超重要（Metalを使わない）
)

# =========================
# ユーティリティ
# =========================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# 質問生成（SEO無限化）
# =========================

def generate_questions(existing_titles: set[str]) -> list[str]:
    prompt = f"""
あなたは恋愛相談専門サイトの編集者です。

以下の条件をすべて守って、
SEOに強い「恋愛相談の質問タイトル」を{GENERATE_COUNT}個生成してください。

条件：
・日本語
・検索されやすい自然な文
・悩みが具体的に想像できる
・疑問文で終わる
・同じ意味の質問は作らない
・既存タイトルと被らない

既存タイトル：
{list(existing_titles)}

出力形式：
・1行に1つ
・番号や記号は付けない
"""

    result = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE
    )

    text = result["choices"][0]["text"]

    titles = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line in existing_titles:
            continue
        titles.append(line)

    return titles

# =========================
# メイン処理
# =========================

def main():
    questions = load_json(QUESTIONS_FILE, [])
    used = load_json(USED_QUESTIONS_FILE, [])

    existing_titles = {
        q["title"] for q in questions
        if isinstance(q, dict) and "title" in q
    }

    new_titles = generate_questions(existing_titles)

    if not new_titles:
        print("⚠ 新しい質問は生成されませんでした")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for title in new_titles:
        questions.append({
            "title": title,
            "created_at": now
        })

    save_json(QUESTIONS_FILE, questions)

    print(f"✅ 新規質問 {len(new_titles)} 件を追加しました")

# =========================

if __name__ == "__main__":
    main()
