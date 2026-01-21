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

def scrape_questions():
    print("知恵袋からお悩みをスキャン中...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('a[class^="ClapItem_cl-clapItem__title"]')
        
        questions = []
        for item in items[:10]: # 最新10件を確認
            questions.append({
                "title": item.get_text(),
                "url": item.get('href')
            })
        return questions
    except Exception as e:
        print(f"Scrape Error: {e}")
        return []

def ai_process(raw_title):
    print(f"結姉さんがお便りをリライト中: {raw_title}")
    try:
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        
        # 厳格なプロンプト：ラジオネーム生成＋リライト＋回答
        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。以下のルールを厳守してください。
1. 相談内容から可愛い「ラジオネーム」を考案してください。
2. 相談内容を「結姉さん、聞いて…」で始まるお便り形式にリライトしてください。
3. 日本語のみを使用し、英語は一切禁止です。
4. 恋愛以外のニュース、芸能、広告、事件は「SKIP」とだけ出力してください。]

相談元ネタ: {raw_title}

出力形式:
RadioName: [考案した名前]
Letter: [リライトした文章]
Answer: [結姉さんの回答]
Description: [SEO用の100文字程度の要約]"""

        output = llm(prompt, max_tokens=1500, temperature=0.7, stop=["[System:"], echo=False)
        text = output['choices'][0]['text'].strip()
        
        if "SKIP" in text: return None
        
        # パース
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
    file_name = f"{today_str}.html"
    
    # 個別記事ページ生成 (post.htmlをベースに流し込み)
    with open("post_template.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("{{TITLE}}", new_data['radio_name'] + "さんからのお便り")
    html = html.replace("{{LETTER}}", new_data['letter'])
    html = html.replace("{{ANSWER}}", new_data['answer'])
    html = html.replace("{{DESCRIPTION}}", new_data['description'])
    html = html.replace("{{DATE}}", display_date)
    
    with open(f"public/posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(html)

    # JSON更新
    db_path = "data/questions.json"
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f: db = json.load(f)
    
    db.insert(0, {
        "title": new_data['radio_name'] + "さんのお悩み",
        "url": f"posts/{file_name}",
        "date": display_date,
        "description": new_data['description']
    })
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:500], f, ensure_ascii=False, indent=4) # 最大500件

def main():
    for d in ["posts", "data", "public/data", "public/posts"]: os.makedirs(d, exist_ok=True)
    
    raw_qs = scrape_questions()
    added_today = 0
    
    db_titles = []
    if os.path.exists("data/questions.json"):
        with open("data/questions.json", "r", encoding="utf-8") as f:
            db_titles = [q['title'] for q in json.load(f)]

    for q in raw_qs:
        if added_today >= 1: break # 1日1件厳選
        processed = ai_process(q['title'])
        if processed:
            update_archive_and_pages(processed)
            added_today += 1

    # 静的ファイルのコピー
    for f in ["index.html", "archive.html", "profile.html", "style.css", "yui.png", "yuichibi.png", "ad_sample.png"]:
        if os.path.exists(f): shutil.copy(f, "public/")
    
    print("全工程完了")

if __name__ == "__main__": main()