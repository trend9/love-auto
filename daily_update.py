import feedparser
import os
import json
from datetime import datetime
from llama_cpp import Llama

RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875"
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10 

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の相談に親身に回答してください。\n\n相談: {question}\n\n回答:"
        output = llm(prompt, max_tokens=800, stop=["相談:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"エラーが発生しました。: {str(e)}"

def main():
    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:BATCH_SIZE]
    
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    questions_data = []
    # 既存データの読み込み
    if os.path.exists("data/questions.json"):
        try:
            with open("data/questions.json", "r", encoding="utf-8") as f:
                questions_data = json.load(f)
        except:
            questions_data = []

    for i, entry in enumerate(entries):
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"posts/{date_str}_{i}.md"
        
        answer = generate_answer(entry.summary)
        content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        questions_data.insert(0, {
            "title": entry.title,
            "file": filename,
            "date": datetime.now().strftime("%Y/%m/%d")
        })

    # 重要：書き込みを確定させる
    json_path = "data/questions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
    
    # ログに出力して確認
    print(f"--- 完了確認 ---")
    print(f"生成ファイル数: {len(entries)}")
    print(f"JSONサイズ: {os.path.getsize(json_path)} bytes")

if __name__ == "__main__":
    main()