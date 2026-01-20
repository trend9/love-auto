import feedparser
import os
import json
import shutil
import sys
import time
from datetime import datetime
from llama_cpp import Llama

# ユーザー指定の「恋愛」キーワードで広範囲に取得するURL
RSS_URLS = [
    "https://news.google.com/rss/search?q=%E6%81%8B%E6%84%9B+when:1d&hl=ja&gl=JP&ceid=JP:ja"
]

MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 15 # 今回は多めに15件を目標にします

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        if not os.path.exists(MODEL_PATH):
            return "モデルが見つからないため、回答できませんでした。"
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        # 結姉さんのキャラクターを維持し、PRを徹底排除
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の恋愛に関するニュースや相談に対して、親身にアドバイスしてください。PRやURLは一切含めないでください。\n\n内容: {question}\n\n結姉さんの回答:"
        output = llm(prompt, max_tokens=1000, stop=["内容:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"エラーが発生しました。: {str(e)}"

def main():
    print("Pythonプログラムを開始します（Googleニュース恋愛特化モード）...")
    
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

    feed = None
    for url in RSS_URLS:
        print(f"ニュースを取得中: {url}")
        temp_feed = feedparser.parse(url, agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        if hasattr(temp_feed, 'entries') and len(temp_feed.entries) > 0:
            print(f"成功！{len(temp_feed.entries)}件のネタを捕捉しました。")
            feed = temp_feed
            break

    if feed and feed.entries:
        new_count = 0
        for entry in feed.entries:
            # 重複チェック
            if any(q['title'] == entry.title for q in questions_data):
                continue
            
            if new_count >= BATCH_SIZE:
                break

            print(f"記事生成 {new_count + 1}/{BATCH_SIZE}: {entry.title}")
            date_str = datetime.now().strftime("%Y%m%d")
            time_suffix = datetime.now().strftime("%H%M%S")
            filename = f"posts/{date_str}_{new_count}_{time_suffix}.md"
            
            # ニュースのタイトルと本文を組み合わせて相談内容とする
            query_text = f"タイトル: {entry.title}\n内容: {getattr(entry, 'summary', '')}"
            answer = generate_answer(query_text)
            
            # Markdown作成（PR排除）
            content = f"# {entry.title}\n\n## 相談内容（ニュース）\n{query_text}\n\n## 結姉さんの回答\n{answer}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            # JSON用データ
            questions_data.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })
            new_count += 1
        
        if new_count > 0:
            # 最新100件を保持
            with open("data/questions.json", "w", encoding="utf-8") as f:
                json.dump(questions_data[:100], f, ensure_ascii=False, indent=4)
            print(f"【大成功】{new_count}件の記事を生成・蓄積しました！")
        else:
            print("新しいネタが見つかりませんでした。")
    else:
        print("ニュースの取得に失敗しました。")

    # 公開用 public フォルダの同期（画像も含めて確実に！）
    print("公開用ファイルを public フォルダに同期中...")
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

    print("SUCCESS: サイト更新の準備が整いました。")

if __name__ == "__main__":
    main()