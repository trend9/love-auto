import feedparser
import os
import json
import shutil
import sys
import time
from datetime import datetime
from llama_cpp import Llama

# 【解決】知恵袋の404を回避し、確実に取れる最新の検索・カテゴリフィード
RSS_URLS = [
    # 知恵袋：恋愛相談カテゴリの最新（新しいRSS生成パラメータ）
    "https://chiebukuro.yahoo.co.jp/rss/category/2078297875",
    # 知恵袋：キーワード「悩み」の最新検索結果
    "https://chiebukuro.yahoo.co.jp/rss/search?p=%E6%81%8B%E6%84%9B+%E6%82%A9%E3%81%BF&flg=3",
    # Googleニュース：恋愛相談の悩み（バックアップ用）
    "https://news.google.com/rss/search?q=%E6%81%8B%E6%84%9B%E7%9B%B8%E8%AB%87+%E6%82%A9%E3%81%BF+when:1d&hl=ja&gl=JP&ceid=JP:ja"
]

MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 1 # 毎日10件ずつ追加

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        if not os.path.exists(MODEL_PATH): return "モデル読み込み失敗"
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の悩みに対し、親身にアドバイスしてください。\n\n内容: {question}\n\n結姉さんの回答:"
        output = llm(prompt, max_tokens=1000, stop=["内容:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"AIエラー: {str(e)}"

def main():
    print("Pythonプログラムを開始します（知恵袋優先・SEO蓄積モード）...")
    
    # 必要なフォルダをすべて作成
    for d in ["posts", "data", "public/data", "public/posts"]:
        os.makedirs(d, exist_ok=True)

    # 既存データの読み込み（全履歴を読み込んで保持する）
    all_questions = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try:
                all_questions = json.load(f)
            except:
                all_questions = []

    # 取得開始
    feed = None
    for url in RSS_URLS:
        print(f"フィード試行中: {url}")
        f = feedparser.parse(url, agent='Mozilla/5.0')
        if f.entries:
            print(f"成功！{len(f.entries)}件取得しました。")
            feed = f
            break
        time.sleep(1)

    if feed and feed.entries:
        new_count = 0
        for entry in feed.entries:
            # 重複チェック（タイトルで判定）
            if any(q['title'] == entry.title for q in all_questions):
                continue
            
            if new_count >= BATCH_SIZE: break

            print(f"新着を処理: {entry.title}")
            date_str = datetime.now().strftime("%Y%m%d")
            time_suffix = datetime.now().strftime("%H%M%S")
            filename = f"posts/{date_str}_{new_count}_{time_suffix}.md"
            
            # 知恵袋の本文またはタイトルを取得
            query_text = getattr(entry, 'summary', entry.title)
            answer = generate_answer(query_text)
            
            # Markdownとして保存
            content = f"# {entry.title}\n\n## 相談内容\n{query_text}\n\n## 結姉さんの回答\n{answer}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            # リストの先頭に追加（最新が一番上）
            all_questions.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })
            new_count += 1
        
        # questions.json を全履歴含めて保存
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=4)
        print(f"累計記事数: {len(all_questions)}件（今回 {new_count}件追加）")

    # 全ファイルを public フォルダに同期
    base_files = ["index.html", "post.html", "style.css", "yui.png", "chibi.png"]
    for f in base_files:
        if os.path.exists(f): shutil.copy(f, "public/")
    
    shutil.copy("data/questions.json", "public/data/questions.json")
    if os.path.exists("posts"):
        for f in os.listdir("posts"):
            shutil.copy(os.path.join("posts", f), "public/posts/")
    print("SUCCESS: 公開用データの準備完了。")

if __name__ == "__main__":
    main()