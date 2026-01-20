import feedparser
import os
import json
import shutil
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
    
    # フォルダ準備
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)
    os.makedirs("public/posts", exist_ok=True)
    
    questions_data = []
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

    # JSON保存
    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
    
    # --- 公開用フォルダ (public) へのコピー ---
    # models フォルダ以外をすべて public に集める
    site_files = ["index.html", "post.html", "style.css"] # 必要に応じて追加
    for file in site_files:
        if os.path.exists(file):
            shutil.copy(file, "public/")
            
    # データと記事をコピー
    shutil.copy("data/questions.json", "public/data/questions.json")
    if os.path.exists("posts"):
        for f in os.listdir("posts"):
            if f.endswith(".md"):
                shutil.copy(os.path.join("posts", f), "public/posts/")

    print(f"完了確認: public フォルダにサイト用ファイルをまとめました。")

if __name__ == "__main__":
    main()