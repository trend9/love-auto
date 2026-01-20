import feedparser
import os
import json
from datetime import datetime
from llama_cpp import Llama

# 設定
RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875" # 恋愛相談カテゴリ
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10  # 一度に10個生成する

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    llm = Llama(model_path=MODEL_PATH, n_ctx=2048)
    prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の恋愛相談に、優しく、時には厳しく、親身に回答してください。PRやURLは一切含めないでください。\n\n相談内容: {question}\n\n回答:"
    output = llm(prompt, max_tokens=1000, stop=["相談内容:"], echo=False)
    return output['choices'][0]['text']

def main():
    if not os.path.exists(MODEL_PATH):
        print(f"モデルが見つかりません: {MODEL_PATH}")
        return

    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:BATCH_SIZE]
    
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    questions_data = []
    # 既存のデータを読み込む
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            questions_data = json.load(f)

    for i, entry in enumerate(entries):
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"posts/{date_str}_{i}.md"
        
        # 既に同じ質問があるかチェック（重複回避）
        if any(q['title'] == entry.title for q in questions_data):
            continue

        answer = generate_answer(entry.summary)
        
        # Markdownファイル作成（PRや元リンクを排除）
        content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        # データを蓄積
        questions_data.insert(0, {
            "title": entry.title,
            "file": filename,
            "date": datetime.now().strftime("%Y/%m/%d")
        })

    # 最新の20件だけ保持
    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)

    print(f"{len(entries)}件の更新が完了しました。")

if __name__ == "__main__":
    main()