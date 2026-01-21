import requests
from bs4 import BeautifulSoup
import os
import json
import shutil
import re
from datetime import datetime
from llama_cpp import Llama

# 設定
TARGET_URL = "https://chiebukuro.yahoo.co.jp/category/2078675272/question/list"
MODEL_PATH = "./models/model.gguf"

# 厳格なNGワードリスト
NG_WORDS = ["キャンペーン", "プレゼント", "実施", "開始", "提供", "円", "割引", "カウンセリング", "PR", "イベント", "ニュース", "undefined"]

def scrape_questions():
    print("知恵袋からお悩みを厳選スキャン中...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('a[class^="ClapItem_cl-clapItem__title"]')
        
        questions = []
        for item in items:
            title = item.get_text()
            # フィルター：NGワードが含まれていたらスキップ
            if any(word in title for word in NG_WORDS):
                continue
            questions.append({
                "title": title,
                "url": item.get('href')
            })
        return questions
    except Exception as e:
        print(f"Scrape Error: {e}")
        return []

def ai_process(raw_title):
    print(f"結姉さんがお便りをリライト中: {raw_title}")
    try:
        if not os.path.exists(MODEL_PATH): return None
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        
        # 指示を強化：広告っぽくても個人の悩みに変換させる
        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。
1. 相談内容から可愛い「ラジオネーム」を考案してください。
2. 相談内容がもしニュースや広告のような硬い文章でも、必ず「一人の悩める女性からの個人的な相談」として、結姉さん、聞いて…で始まるお便り形式にリライトしてください。
3. 日本語のみ。英語禁止。]

相談元ネタ: {raw_title}

出力形式:
RadioName: [考案した名前]
Letter: [リライトした文章]
Answer: [結姉さんの回答]
Description: [SEO用の100文字程度の要約]"""

        output = llm(prompt, max_tokens=1500, temperature=0.7, stop=["[System:"], echo=False)
        text = output['choices'][0]['text'].strip()
        
        res = {}
        for line in text.split('\n'):
            if line.startswith('RadioName:'): res['radio_name'] = line.replace('RadioName:', '').strip()
            if line.startswith('Letter:'): res['letter'] = line.replace('Letter:', '').strip()
            if line.startswith('Answer:'): res['answer'] = line.replace('Answer:', '').strip()
            if line.startswith('Description:'): res['description'] = line.replace('Description:', '').strip()
        
        return res if len(res) >= 4 else None
    except:
        return None

def update_archive_and_pages(new_data):
    today_str = datetime.now().strftime("%Y%m%d")
    display_date = datetime.now().strftime("%Y/%m/%d")
    # 404防止のため、生成されるパスとJSONのurlを一致させる
    file_name = f"{today_str}.html"
    
    with open("post_template.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("{{TITLE}}", new_data['radio_name'] + "さんからのお便り")
    html = html.replace("{{LETTER}}", new_data['letter'])
    html = html.replace("{{ANSWER}}", new_data['answer'])
    html = html.replace("{{DESCRIPTION}}", new_data['description'])
    html = html.replace("{{DATE}}", display_date)
    
    # public/posts/ 内に実ファイルを作成
    with open(f"public/posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(html)

    db_path = "data/questions.json"
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = []
    
    # JSONに保存するURLを "posts/ファイル名" に固定（index.htmlから見て正しいパス）
    db.insert(0, {
        "title": new_data['radio_name'] + "さんのお悩み",
        "url": f"posts/{file_name}",
        "date": display_date,
        "description": new_data['description']
    })
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:500], f, ensure_ascii=False, indent=4)

def main():
    for d in ["posts", "data", "public/data", "public/posts"]: os.makedirs(d, exist_ok=True)
    
    raw_qs = scrape_questions()
    added_today = 0
    
    for q in raw_qs:
        if added_today >= 1: break
        processed = ai_process(q['title'])
        if processed:
            update_archive_and_pages(processed)
            added_today += 1

    # 静的ファイルをすべてpublicへ
    for f in ["index.html", "archive.html", "profile.html", "post.html", "post_template.html", "style.css", "yui.png", "yuichibi.png", "ad_sample.png"]:
        if os.path.exists(f): shutil.copy(f, "public/")
    
    if os.path.exists("data/questions.json"):
        shutil.copy("data/questions.json", "public/data/questions.json")

if __name__ == "__main__": main()