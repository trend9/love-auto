import requests
from bs4 import BeautifulSoup
import os
import json
import shutil
from datetime import datetime
from llama_cpp import Llama

# 設定
TARGET_URL = "https://chiebukuro.yahoo.co.jp/category/2078675272/question/list"
MODEL_PATH = "./models/model.gguf"
NG_WORDS = ["キャンペーン", "プレゼント", "実施", "開始", "提供", "円", "割引", "カウンセラー", "PR", "イベント", "ニュース", "アットプレス", "ウォーカープラス", "undefined"]

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
            if any(word in title for word in NG_WORDS): continue
            questions.append({"title": title, "url": item.get('href')})
        return questions
    except: return []

def ai_process(raw_title):
    print(f"結姉さんがお便りをリライト中: {raw_title}")
    try:
        if not os.path.exists(MODEL_PATH): return None
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。1.可愛いラジオネームを考案。2.お便り形式にリライト。3.日本語のみ。]
相談元ネタ: {raw_title}
出力形式:
RadioName: [名前]
Letter: [文章]
Answer: [回答]
Description: [要約]"""
        output = llm(prompt, max_tokens=1000, temperature=0.7, stop=["[System:"], echo=False)
        text = output['choices'][0]['text'].strip()
        res = {}
        for line in text.split('\n'):
            if line.startswith('RadioName:'): res['radio_name'] = line.replace('RadioName:', '').strip()
            if line.startswith('Letter:'): res['letter'] = line.replace('Letter:', '').strip()
            if line.startswith('Answer:'): res['answer'] = line.replace('Answer:', '').strip()
            if line.startswith('Description:'): res['description'] = line.replace('Description:', '').strip()
        return res if len(res) >= 4 else None
    except: return None

def update_files(new_data):
    today_str = datetime.now().strftime("%Y%m%d")
    display_date = datetime.now().strftime("%Y/%m/%d")
    file_name = f"{today_str}.html"
    os.makedirs("posts", exist_ok=True)
    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    content = template.replace("{{TITLE}}", new_data['radio_name'] + "さんからのお便り")\
                      .replace("{{LETTER}}", new_data['letter'])\
                      .replace("{{ANSWER}}", new_data['answer'])\
                      .replace("{{DESCRIPTION}}", new_data['description'])\
                      .replace("{{DATE}}", display_date)
    with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(content)
    os.makedirs("data", exist_ok=True)
    db_path = "data/questions.json"
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = []
    db.insert(0, {"title": new_data['radio_name'] + "さんのお悩み", "url": f"posts/{file_name}", "date": display_date, "description": new_data['description']})
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:500], f, ensure_ascii=False, indent=4)

def main():
    raw_qs = scrape_questions()
    for q in raw_qs:
        processed = ai_process(q['title'])
        if processed:
            update_files(processed)
            break 

if __name__ == "__main__": main()