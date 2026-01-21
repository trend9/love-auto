import os
import json
import random
import re
from datetime import datetime, timedelta
from llama_cpp import Llama

# 設定
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 20

def ai_generate_letter(llm, index):
    print(f"結姉さんが{index+1}通目を執筆中...")
    themes = ["片思い 連絡 頻度", "既婚者 好き 諦め方", "元カレ 復縁 可能性", "マッチングアプリ 初対面 会話", "社内恋愛 秘密 バレる", "彼氏 浮気 兆候", "30代 結婚 焦り", "マッチングアプリ 2回目 誘われない"]
    theme = random.choice(themes)

    try:
        # プロンプトに「SEOタイトル」の項目を追加
        prompt = f"""[System: 日本人女性の結姉さん。SEOを意識した日本語で回答して。]
テーマ: {theme}
RadioName: 
Letter: 結姉さん、聞いて…
Answer: 
Description: (検索されやすい100文字程度の要約)
SEOTitle: (検索キーワードを含めた32文字以内の魅力的なタイトル)
---"""
        output = llm(prompt, max_tokens=1000, temperature=0.7, stop=["---"])
        text = output['choices'][0]['text'].strip()
        
        res = {"radio_name": f"匿名さん_{index}", "letter": "", "answer": "", "description": "", "seo_title": ""}
        for line in text.split('\n'):
            if 'RadioName:' in line: res['radio_name'] = line.split(':', 1)[1].strip()
            if 'Letter:' in line: res['letter'] = line.split(':', 1)[1].strip()
            if 'Answer:' in line: res['answer'] = line.split(':', 1)[1].strip()
            if 'Description:' in line: res['description'] = line.split(':', 1)[1].strip()
            if 'SEOTitle:' in line: res['seo_title'] = line.split(':', 1)[1].strip()

        # SEOタイトルのバックアップ（AIが失敗した時用）
        if not res['seo_title']:
            res['seo_title'] = f"{theme}の悩み相談"
            
        return res
    except:
        return None

def update_system(new_data_list):
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    db_path = "data/questions.json"
    db = []
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = []

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    for i, data in enumerate(new_data_list):
        time_suffix = (now + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        display_date = now.strftime("%Y/%m/%d %H:%M")
        file_name = f"{time_suffix}.html"
        
        # タイトルを「AIが考えたSEOタイトル」に差し替え！
        full_seo_title = f"{data['seo_title']} | 結姉さんの恋愛相談所"
        
        content = template.replace("{{SEO_TITLE}}", full_seo_title)\
                          .replace("{{SEO_DESCRIPTION}}", data['description'])\
                          .replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", data['letter'])\
                          .replace("{{ANSWER}}", data['answer'])\
                          .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(content)

        db.insert(0, {
            "title": data['seo_title'], # JSON側のリスト表示もSEOタイトルにする
            "url": f"posts/{file_name}",
            "date": display_date,
            "description": data['description']
        })

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:1000], f, ensure_ascii=False, indent=4)

def main():
    if not os.path.exists(MODEL_PATH): return
    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)
    
    generated_results = []
    for i in range(GENERATE_COUNT):
        res = ai_generate_letter(llm, i)
        if res:
            generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"成功：{len(generated_results)}件のSEO最適化記事を生成したわ。")

if __name__ == "__main__":
    main()