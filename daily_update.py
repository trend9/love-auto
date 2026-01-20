import feedparser, os, json, shutil, time
from datetime import datetime
from llama_cpp import Llama

RSS_URLS = [
    "https://chiebukuro.yahoo.co.jp/rss/search?p=%E6%81%8B%E6%84%9B+%E7%9B%B8%E8%AB%87&flg=3",
    "https://news.google.com/rss/search?q=%E6%81%8B%E6%84%9B%E7%9B%B8%E8%AB%87+%E6%82%A9%E3%81%BF+-映画+-主演+-出演&hl=ja&gl=JP&ceid=JP:ja"
]
MODEL_PATH = "./models/model.gguf"
BATCH_SIZE = 10 # 動作確認用。成功したら5〜10に。

def generate_answer(question):
    print("日本語回答を生成中...")
    try:
        if not os.path.exists(MODEL_PATH): return "AI準備中"
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        # 英語回答を禁止する強力なプロンプト
        prompt = f"あなたは包容力のある日本の女性『結姉さん』です。以下の相談に必ず「日本語」で親身に答えてください。英語は絶対に使わないでください。\n\n相談: {question}\n\n結姉さんの回答（日本語）:"
        output = llm(prompt, max_tokens=1000, stop=["相談:", "User:"], echo=False)
        return output['choices'][0]['text'].strip()
    except Exception as e: return f"エラー: {str(e)}"

def main():
    # フォルダ生成
    for d in ["posts", "data", "public/data", "public/posts"]:
        os.makedirs(d, exist_ok=True)

    # 履歴読み込み
    all_q = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            try: all_q = json.load(f)
            except: all_q = []

    # 取得と生成
    feed = None
    for url in RSS_URLS:
        f = feedparser.parse(url, agent='Mozilla/5.0')
        if f.entries: feed = f; break

    if feed:
        added = 0
        for e in feed.entries:
            # 芸能ニュース除外
            if any(w in e.title for w in ["映画", "主演", "出演", "リリース"]): continue
            if any(q['title'] == e.title for q in all_q): continue
            if added >= BATCH_SIZE: break

            fname = f"posts/{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            body = getattr(e, 'summary', e.title)
            ans = generate_answer(body)
            
            with open(fname, "w", encoding="utf-8") as f:
                f.write(f"# {e.title}\n\n## 相談内容\n{body}\n\n## 結姉さんの回答\n{ans}")
            
            all_q.insert(0, {"title": e.title, "file": fname, "date": datetime.now().strftime("%Y/%m/%d")})
            added += 1
            
        with open("data/questions.json", "w", encoding="utf-8") as f:
            json.dump(all_q, f, ensure_ascii=False, indent=4)

    # 全ファイルを public フォルダへ同期（ここがSEOと表示の鍵）
    for f in ["index.html", "post.html", "profile.html", "style.css", "yui.png", "yuichibi.png"]:
        if os.path.exists(f): shutil.copy(f, "public/")
    shutil.copy("data/questions.json", "public/data/questions.json")
    if os.path.exists("posts"):
        for f in os.listdir("posts"):
            shutil.copy(os.path.join("posts", f), "public/posts/")
    print("SUCCESS: Archive Updated")

if __name__ == "__main__": main()