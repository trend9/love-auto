import requests
from bs4 import BeautifulSoup
import os
import json
import shutil
import random
from datetime import datetime
from llama_cpp import Llama

# 設定
TARGET_URL = "https://chiebukuro.yahoo.co.jp/category/2078675272/question/list"
MODEL_PATH = "./models/model.gguf"
# フィルターを少し緩和しつつ、PRサイト名はしっかり弾く
NG_WORDS = ["アットプレス", "ウォーカープラス", "PR TIMES", "キャンペーン", "実施", "開始", "提供", "円", "割引", "undefined"]

def scrape_questions():
    print("知恵袋からお悩みをスキャン中...")
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # Yahoo知恵袋の現在のセレクタに合わせる
        items = soup.select('a[href*="/question/"]')
        
        questions = []
        for item in items:
            title = item.get_text().strip()
            if len(title) < 15: continue # 短すぎるタイトルはスキップ
            if any(word in title for word in NG_WORDS): continue
            questions.append({"title": title, "url": item.get('href')})
        
        print(f"{len(questions)}件の候補を見つけたわ。")
        return questions
    except Exception as e:
        print(f"Scrape Error: {e}")
        return []

def ai_process(raw_title=None):
    """
    raw_titleがある場合はそれをリライト。
    Noneの場合はAIが自らお悩みを作成する。
    """
    mode = "リライト" if raw_title else "新規作成"
    print(f"結姉さんがお便りを{mode}中...")
    
    try:
        if not os.path.exists(MODEL_PATH): return None
        llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)
        
        if raw_title:
            prompt_content = f"相談元ネタ: {raw_title}"
        else:
            prompt_content = "相談元ネタ: (なし。現代の20代女性が抱きそうなリアルな恋愛の悩みを1つ考えてください)"

        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。
1. 可愛い「ラジオネーム」を考案してください。
2. {prompt_content}
3. 上記を「結姉さん、聞いて…」で始まる、一人の女性からの個人的なお悩み（お便り形式）にしてください。
4. 結姉さんとして優しく、時に厳しく回答を書いてください。
5. 日本語のみ。出力は以下の形式を厳守。]

出力形式:
RadioName: [考案した名前]
Letter: [お便り文章]
Answer: [結姉さんの回答]
Description: [100文字要約]"""

        output = llm(prompt, max_tokens=1500, temperature=0.8, stop=["[System:"], echo=False)
        text = output['choices'][0]['text'].strip()
        
        res = {}
        for line in text.split('\n'):
            if line.startswith('RadioName:'): res['radio_name'] = line.replace('RadioName:', '').strip()
            if line.startswith('Letter:'): res['letter'] = line.replace('Letter:', '').strip()
            if line.startswith('Answer:'): res['answer'] = line.replace('Answer:', '').strip()
            if line.startswith('Description:'): res['description'] = line.replace('Description:', '').strip()
        
        # 必須項目が欠けていたら失敗
        if not all(k in res for k in ['radio_name', 'letter', 'answer', 'description']):
            return None
            
        return res
    except:
        return None

def update_files(new_data):
    today_str = datetime.now().strftime("%Y%m%d")
    display_date = datetime.now().strftime("%Y/%m/%d")
    file_name = f"{today_str}.html"
    
    os.makedirs("posts", exist_ok=True)
    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    html_content = template.replace("{{TITLE}}", new_data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", new_data['letter'])\
                          .replace("{{ANSWER}}", new_data['answer'])\
                          .replace("{{DESCRIPTION}}", new_data['description'])\
                          .replace("{{DATE}}", display_date)
    
    with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
        f.write(html_content)

    os.makedirs("data", exist_ok=True)
    db_path = "data/questions.json"
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = []
    
    # 重複チェック（今日の日付のファイルがあれば上書きせずスキップする設定も可能）
    db.insert(0, {
        "title": new_data['radio_name'] + "さんのお悩み",
        "url": f"posts/{file_name}",
        "date": display_date,
        "description": new_data['description']
    })
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:500], f, ensure_ascii=False, indent=4)
    return file_name

def main():
    raw_qs = scrape_questions()
    
    # まずスクレイピング結果から試す
    processed = None
    if raw_qs:
        for q in raw_qs:
            processed = ai_process(q['title'])
            if processed: break
    
    # もしスクレイピングで全滅、または候補がなかった場合
    if not processed:
        print("お悩みが拾えなかったから、結姉さんが自分で考えるわね。")
        processed = ai_process(None) # 自作モード
    
    if processed:
        file_generated = update_files(processed)
        print(f"記事生成完了: {file_generated}")
    else:
        print("致命的なエラー：記事が生成できなかったわ。")

if __name__ == "__main__":
    main()