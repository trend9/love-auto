import feedparser
import os
import json
import shutil
import sys
from datetime import datetime
from llama_cpp import Llama

# 設定（より安定したURLに変更：知恵袋 恋愛相談カテゴリ全体）
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

    # 既存データの読み込み（重複チェック用）
    questions_data = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                questions_data = json.load(f)
            except:
                questions_data = []

    # RSSの取得
    print(f"RSSを取得中: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if feed.entries:
        new_count = 0
        for entry in feed.entries:
            # 重複チェック：すでに同じタイトルの記事があればスキップ
            if any(q['title'] == entry.title for q in questions_data):
                continue
            
            # 最大取得件数に達したら終了
            if new_count >= BATCH_SIZE:
                break

            print(f"新着記事を発見: {entry.title}")
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"posts/{date_str}_{new_count}.md"
            
            # AI回答生成
            answer = generate_answer(entry.summary)
            
            # ファイル保存
            content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            # リストの先頭に追加
            questions_data.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })
            new_count += 1
        
        if new_count > 0:
            # 最新50件のみ保持して保存
            with open("data/questions.json", "w", encoding="utf-8") as f:
                json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
            print(f"{new_count}件の新しい記事を追加しました。")
        else:
            print("新しい相談はありませんでした（すべて取得済み）。")
    else:
        print("警告: RSSフィードが取得できませんでした。知恵袋側が一時的に制限している可能性があります。")

    # サイト公開用ファイルのコピー（404回避）
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

    print("SUCCESS: すべての準備が完了しました。")

if __name__ == "__main__":
    main()