import feedparser
import os
import json
import shutil
import sys
from datetime import datetime
from llama_cpp import Llama

RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875"
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10 

def generate_answer(question):
    print(f"回答を生成中: {question[:30]}...")
    try:
        # モデルが存在するか再確認
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"モデルファイルがありません: {MODEL_PATH}")
            
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=True)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の相談に親身に回答してください。\n\n相談: {question}\n\n回答:"
        output = llm(prompt, max_tokens=800, stop=["相談:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        print(f"ERROR: 回答生成中に問題が発生しました: {str(e)}")
        raise e # エラーを隠さず、プログラムを止める

def main():
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("RSSの取得に失敗したか、記事がありません。")
            return

        entries = feed.entries[:BATCH_SIZE]
        
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
        
        # publicへのコピー
        for f in ["index.html", "post.html", "style.css", "yui.png", "chibi.png"]:
            if os.path.exists(f):
                shutil.copy(f, "public/")
        
        shutil.copy("data/questions.json", "public/data/questions.json")
        for f in os.listdir("posts"):
            if f.endswith(".md"):
                shutil.copy(os.path.join("posts", f), "public/posts/")

        print(f"SUCCESS: {len(entries)}件の記事を処理しました。")
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        sys.exit(1) # GitHub Actionsに「失敗した」と明示的に伝える

if __name__ == "__main__":
    main()