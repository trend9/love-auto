import feedparser
import os
import json
import shutil
import sys
import time
from datetime import datetime
from llama_cpp import Llama

# 意地でも捕まえるためのURLリスト
RSS_URLS = [
    "https://chiebukuro.yahoo.co.jp/rss/2078297875", # 恋愛相談カテゴリ全体
    "https://chiebukuro.yahoo.co.jp/rss/2078676154", # 恋愛悩み相談
    "https://chiebukuro.yahoo.co.jp/rss/2079459312"  # 片思い
]

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
    print("Pythonプログラムを開始します（執念モード）...")
    
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)
    os.makedirs("public/posts", exist_ok=True)

    questions_data = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                questions_data = json.load(f)
            except:
                questions_data = []

    # 意地でもデータを取るためのループ
    feed = None
    for url in RSS_URLS:
        print(f"RSSを試行中: {url}")
        # ブラウザのふりをしてアクセス
        temp_feed = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        if temp_feed.entries:
            print(f"成功！{len(temp_feed.entries)}件のデータを捕捉しました。")
            feed = temp_feed
            break
        else:
            print("取得失敗。次のURLを試します...")
            time.sleep(2) # 2秒待ってから次へ

    if feed and feed.entries:
        new_count = 0
        for entry in feed.entries:
            if any(q['title'] == entry.title for q in questions_data):
                continue
            
            if new_count >= BATCH_SIZE:
                break

            print(f"新着を処理開始: {entry.title}")
            date_str = datetime.now().strftime("%Y%m%d")
            # 重複ファイル名回避のため秒まで入れる
            time_suffix = datetime.now().strftime("%H%M%S")
            filename = f"posts/{date_str}_{new_count}_{time_suffix}.md"
            
            answer = generate_answer(entry.summary)
            
            content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            questions_data.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })
            new_count += 1
        
        if new_count > 0:
            with open("data/questions.json", "w", encoding="utf-8") as f:
                json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
            print(f"【祝】{new_count}件の新着記事を捕まえ、生成に成功しました！")
        else:
            print("新着はありませんでした（すべて取得済みです）。")
    else:
        print("【全滅】すべてのRSSが空でした。知恵袋のブロックが非常に強力です。")

    # 公開準備
    print("publicフォルダを更新中...")
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

    print("SUCCESS: サイト更新完了。")

if __name__ == "__main__":
    main()