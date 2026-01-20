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
        # モデルが存在するか確認
        if not os.path.exists(MODEL_PATH):
            print(f"ERROR: モデルファイルが {MODEL_PATH} に見つかりません。")
            return "モデルが見つからないため、回答できませんでした。"
            
        # AIモデルの読み込み
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=True)
        prompt = f"あなたは包容力のある年上の女性『結（ゆい）姉さん』です。以下の相談に親身に回答してください。PRやURLは一切含めないでください。\n\n相談内容: {question}\n\n回答:"
        
        output = llm(prompt, max_tokens=800, stop=["相談内容:"], echo=False)
        return output['choices'][0]['text']
    except Exception as e:
        print(f"AI生成エラー: {str(e)}")
        return f"回答生成中にエラーが発生しました。: {str(e)}"

def main():
    print("Pythonプログラムを開始します...")
    
    # フォルダの強制作成
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("public/data", exist_ok=True)
    os.makedirs("public/posts", exist_ok=True)

    try:
        # RSSフィードの取得
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            print("RSSフィードが空です。")
            return

        entries = feed.entries[:BATCH_SIZE]
        
        # 既存データの読み込み
        questions_data = []
        if os.path.exists("data/questions.json"):
            with open("data/questions.json", "r", encoding="utf-8") as f:
                try:
                    questions_data = json.load(f)
                except:
                    questions_data = []

        # 記事生成ループ
        for i, entry in enumerate(entries):
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"posts/{date_str}_{i}.md"
            
            # 回答生成
            answer = generate_answer(entry.summary)
            
            # Markdownファイルの保存
            content = f"# {entry.title}\n\n## 相談内容\n{entry.summary}\n\n## 結姉さんの回答\n{answer}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            # JSON用データ蓄積
            questions_data.insert(0, {
                "title": entry.title,
                "file": filename,
                "date": datetime.now().strftime("%Y/%m/%d")
            })

        # 全体のJSONを保存
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(questions_data[:50], f, ensure_ascii=False, indent=4)
        
        # --- publicフォルダ（公開用）へのコピー ---
        print("公開用ファイルを準備しています...")
        base_files = ["index.html", "post.html", "style.css", "yui.png", "chibi.png"]
        for f in base_files:
            if os.path.exists(f):
                shutil.copy(f, "public/")
            else:
                print(f"警告: {f} が見つからないためコピーをスキップしました。")
        
        # データのコピー
        shutil.copy("data/questions.json", "public/data/questions.json")
        for f in os.listdir("posts"):
            if f.endswith(".md"):
                shutil.copy(os.path.join("posts", f), "public/posts/")

        print("SUCCESS: すべての処理が完了しました。")

    except Exception as e:
        print(f"致命的なエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()