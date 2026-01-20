import feedparser
import os
import json
from datetime import datetime
from llama_cpp import Llama

# 設定
RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875"
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10 

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    # モデルの読み込み（ここで失敗する場合はメモリ不足の可能性あり）
    try:
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の恋愛相談に、優しく、親身に回答してください。PRやURLは一切含めないでください。\n\n相談内容: {question}\n\n回答:"
        output = llm(prompt, max_tokens=1000, stop=["相談内容:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"申し訳ありません、回答生成中にエラーが発生しました。: {str(e)}"

def main():
    if not os.path.exists(MODEL_PATH):
        print(f"モデルが見つかりません: {MODEL_PATH}")
        return

    feed = feedparser.parse(RSS_URL)
    entries = feed.entries[:BATCH_SIZE]
    
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    questions_data = []
    if os.path.exists("data/questions.json"):
        try:
            with open("data/questions.json", "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    questions_data = json.loads(content)
        except:
            questions_data = []

    for i, entry in enumerate(entries):
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"posts/{date_str}_{i}.md"
        
        # 重複チェックを一時的に無効化して確実に生成させる
        answer = generate_answer(entry.summary)
        
        content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        questions_data.insert(0, {
            "title": entry.title,
            "file": filename,
            "date": datetime.now().strftime("%Y/%m/%d")
        })

    # データを保存（ここが空だと表示されません）
    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
    
    print(f"完了: {len(entries)}件の記事を生成し、JSONを更新しました。")

if __name__ == "__main__":
    main()