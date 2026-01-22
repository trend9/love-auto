import json
import os
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

QUESTIONS_FILE = DATA_DIR / "questions.json"
USED_FILE = DATA_DIR / "used_questions.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MODEL = "gpt-4o-mini"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ----------------------
# utility
# ----------------------
def load_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ----------------------
# GitHub Models
# ----------------------
def github_llm(prompt: str) -> list:
    url = "https://models.inference.ai.azure.com/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "あなたは恋愛相談サイト向けに"
                    "SEOに強く、検索されやすい質問を作る専門家です。"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.95,
        "max_tokens": 1200
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    return [line.strip("・- ") for line in text.split("\n") if line.strip()]

# ----------------------
# main
# ----------------------
def main():
    questions = load_json(QUESTIONS_FILE)
    used = load_json(USED_FILE)

    # title があるものだけ使う（←超重要）
    existing_titles = {
        q["title"] for q in questions
        if isinstance(q, dict) and "title" in q
    }
    used_titles = {
        q["title"] for q in used
        if isinstance(q, dict) and "title" in q
    }

    prompt = """
恋愛相談サイト向けに、
Google検索で実際に検索されやすい質問を10個作ってください。

条件：
・具体的で悩みが想像できる
・同じ意味の質問は作らない
・タイトル文だけ出力
"""

    titles = github_llm(prompt)

    added = 0
    for t in titles:
        if t in existing_titles or t in used_titles:
            continue

        questions.append({
            "title": t,
            "body": f"{t}。どうすればいいでしょうか？"
        })
        added += 1

    save_json(QUESTIONS_FILE, questions)
    print(f"✅ {added} 件の質問を追加しました")

if __name__ == "__main__":
    main()
