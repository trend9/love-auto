import feedparser
import os
import json
import shutil
import sys
from datetime import datetime
from llama_cpp import Llama

# 設定
RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875"
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10 

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        if not os.path.exists(MODEL_PATH):
            return "モデルが見つからないため、回答できませんでした。"
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の相談に親身に回答してください。\n\n相談内容: {question}\n\n回答:"
        output = llm(prompt, max_tokens=800, stop=["相談内容:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"エラーが発生しました。: {str(e)}"

def main():
    print("Pythonプログラムを開始します...")
    
    # フォルダの強制作成
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)
    os.makedirs("public/posts", exist_ok=True)

    # 1. RSSの取得を試みる
    feed = feedparser.parse(RSS_URL)
    
    # RSSが取得できた場合のみ記事を生成
    if feed.entries:
        entries = feed.entries[:BATCH_SIZE]
        questions_data = []
        if os.path.exists("data/questions.json"):
            with open("data/questions.json", "r", encoding="utf-8") as f:
                try:
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
        
        # JSON保存
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
    else:
        print("警告: RSSフィードが空でした。新規記事の生成をスキップします。")

    # 2. 記事の有無にかかわらず、既存のファイルを public にコピー（404対策）
    print("サイトファイルを public フォルダに配置中...")
    base_files = ["index.html", "post.html", "style.css", "yui.png", "chibi.png"]
    for f in base_files:
        if os.path.exists(f):
            shutil.copy(f, "public/")
    
    if os.path.exists("data/questions.json"):
        shutil.copy("data/questions.json", "public/data/questions.json")
    
    if os.path.exists("posts"):
        for f in os.listdir("posts"):
            if f.endswith(".md"):
                shutil.copy(os.path.join("posts", f), "public/posts/")

    print("SUCCESS: public フォルダの準備が完了しました。")

if __name__ == "__main__":
    main()