import feedparser
import os
import re
from llama_cpp import Llama
from datetime import datetime

# 1. フォルダを確実に作成する
POSTS_DIR = "posts"
os.makedirs(POSTS_DIR, exist_ok=True)

# 2. AIモデルのロード
print("AIモデルを読み込み中...")
try:
    llm = Llama(
        model_path="./models/model.gguf",
        n_ctx=512,
        n_threads=2
    )
except Exception as e:
    print(f"モデルのロードに失敗: {e}")
    exit(1)

# 3. 知恵袋RSSから悩み取得
RSS_URL = "https://chiebukuro.yahoo.co.jp/rss/2078297875/all.xml"
feed = feedparser.parse(RSS_URL)

if not feed.entries:
    print("RSSからデータを取得できませんでした。")
    # テスト用にダミー記事を作成（空エラーを避けるため）
    feed.entries = [type('obj', (object,), {'title': 'テスト相談', 'summary': 'マッチングアプリで返信が来ない！', 'link': 'https://example.com'})]

def generate_ai_answer(question_text):
    prompt = f"### System: あなたは親身な恋愛アドバイザー「あねご」です。関西弁で短く答えて。最後にアプリを勧めて。\n### User: {question_text}\n### Assistant:"
    output = llm(prompt, max_tokens=200, stop=["###"])
    return output['choices'][0]['text'].strip()

# 記事の生成
count = 0
for entry in feed.entries[:10]:
    title = entry.title
    clean_title = re.sub(r'[\\/:*?"<>|]', '', title)[:20]
    filename = os.path.join(POSTS_DIR, f"{datetime.now().strftime('%Y%m%d')}_{count}.md")
    
    print(f"記事作成中: {title}")
    answer = generate_ai_answer(entry.summary)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"## 相談内容\n{entry.summary}\n\n")
        f.write(f"## あねごのアドバイス\n{answer}\n\n")
        f.write(f"---\n[元の相談を詳しく見る]({entry.link})\n")
        f.write("\n\n---\n**【PR】今の恋に行き詰まったら、心機一転マッチングアプリで探そ！**\n")
        f.write("[おすすめのアプリ一覧はこちら](https://your-link.com)")
    count += 1

print(f"{count}件の記事を作成しました。")
