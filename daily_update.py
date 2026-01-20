import feedparser
import os
import json
import shutil
import sys
import time
from datetime import datetime
from llama_cpp import Llama

# 取得先
RSS_URLS = [
    "https://chiebukuro.yahoo.co.jp/rss/category/2078297875",
    "https://chiebukuro.yahoo.co.jp/rss/search?p=%E6%81%8B%E6%84%9B+%E6%82%A9%E3%81%BF&flg=3",
    "https://news.google.com/rss/search?q=%E6%81%8B%E6%84%9B%E7%9B%B8%E8%AB%87+%E6%82%A9%E3%81%BF+when:1d&hl=ja&gl=JP&ceid=JP:ja"
]

MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 1 # 今回は1件設定。通常運用時は10件などに。

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        if not os.path.exists(MODEL_PATH): return "モデルが見つかりません"
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の恋愛相談に親身に回答してください。PRやURLは含めないでください。\n\n相談: {question}\n\n回答:"
        output = llm(prompt, max_tokens=1000, stop=["相談:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        return f"AIエラー: {str(e)}"

def main():
    print("Pythonプログラムを開始します...")
    for d in ["posts", "data", "public/data", "public/posts"]:
        os.makedirs(d, exist_ok=True)

    # 全履歴の読み込み
    all_questions = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try: all_questions = json.load(f)
            except: all_questions = []

    feed = None
    for url in RSS_URLS:
        print(f"試行: {url}")
        f = feedparser.parse(url, agent='Mozilla/5.0')
        if f.entries:
            feed = f
            break

    if feed and feed.entries:
        new_count = 0
        for entry in feed.entries:
            if any(q['title'] == entry.title for q in all_questions): continue
            if new_count >= BATCH_SIZE: break

            print(f"新着: {entry.title}")
            date_str = datetime.now().strftime("%Y%m%d")
            time_suffix = datetime.now().strftime("%H%M%S")
            filename = f"posts/{date_str}_{new_count}_{time_suffix}.md"
            
            body = getattr(entry, 'summary', entry.title)
            answer = generate_answer(body)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {entry.title}\n\n## 相談内容\n{body}\n\n## 結姉さんの回答\n{answer}")
            
            all_questions.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })
            new_count += 1
        
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=4)

    # 公開準備（アーカイブ含め全コピー）
    for f in ["index.html", "post.html", "style.css", "yui.png", "chibi.png"]:
        if os.path.exists(f): shutil.copy(f, "public/")
    shutil.copy("data/questions.json", "public/data/questions.json")
    if os.path.exists("posts"):
        for f in os.listdir("posts"):
            shutil.copy(os.path.join("posts", f), "public/posts/")
    print("SUCCESS: 完了")

if __name__ == "__main__":
    main()