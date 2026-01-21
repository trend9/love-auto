import os
import json
import shutil
import random
import re
from datetime import datetime, timedelta
from llama_cpp import Llama

# 設定
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 20

def ai_generate_letter(llm, index):
    print(f"結姉さんが{index+1}通目のお便りを執筆中...")
    
    themes = ["既婚者の彼との恋", "マッチングアプリで会った人の嘘", "元カレへの未練", "職場の年下男性との距離感", "結婚を渋る彼への不信感", "誰にも言えない秘密の恋", "マッチングアプリ疲れ", "音信不通の理由", "同棲中のマンネリ", "親に反対されている恋"]
    theme = random.choice(themes)

    try:
        # AIに具体的な「役割」と「禁止事項」を徹底
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは日本の「結姉さん（ゆいねえさん）」という、ラジオパーソナリティのような包容力のある女性です。
【絶対厳守】
1. ラジオネームは必ず「ひらがな」や「カタカナ」を使った、一人の女性らしい名前にしてください（例：ゆずき、メロンパンなど）。テーマ名を名前にしないでください。
2. Letter（お悩み）は「結姉さん、聞いて…」から始め、状況が目に浮かぶように具体的に日本語で書いてください（300文字程度）。
3. Answer（回答）は、相談者の心に寄り添い、時に優しく、時に鋭くアドバイスしてください（400文字程度）。定型文は禁止です。
4. すべて日本語で出力してください。
5. 記号(*, [], #)は一切使わないでください。<|eot_id|><|start_header_id|>user<|end_header_id|>
テーマ「{theme}」について、一人のお悩み相談を書き上げてください。<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RadioName:"""

        output = llm(prompt, max_tokens=1500, temperature=0.85, stop=["<|eot_id|>"])
        full_text = "RadioName:" + output['choices'][0]['text'].strip()
        
        res = {}
        for line in full_text.split('\n'):
            line = line.replace('*', '').replace('[', '').replace(']', '').replace('#', '').strip()
            if 'RadioName:' in line: res['radio_name'] = line.split(':', 1)[1].strip()
            if 'Letter:' in line: res['letter'] = line.split(':', 1)[1].strip()
            if 'Answer:' in line: res['answer'] = line.split(':', 1)[1].strip()
            if 'Description:' in line: res['description'] = line.split(':', 1)[1].strip()
        
        # 検閲: 項目欠け、またはテーマ名がRadioNameに含まれている場合
        if len(res) < 4 or theme in res.get('radio_name', ''):
            return None
        
        # 英語混入チェック
        if len(re.findall(r'[a-zA-Z]', res.get('answer', ''))) > 15:
            return None

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

    # テンプレート読み込み
    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    
    for i, data in enumerate(new_data_list):
        time_suffix = (now + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        display_date = now.strftime("%Y/%m/%d %H:%M")
        file_name = f"{time_suffix}.html"
        
        # SEO用タイトルと説明文（AIが生成したものを利用）
        seo_title = f"{data['radio_name']}さんのお悩み相談「{data['description'][:20]}...」 | 結姉さんの恋愛相談所"
        seo_desc = data['description']
        
        # HTML置換（SEOメタタグ部分も含む）
        content = template.replace("{{SEO_TITLE}}", seo_title)\
                          .replace("{{SEO_DESCRIPTION}}", seo_desc)\
                          .replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", data['letter'])\
                          .replace("{{ANSWER}}", data['answer'])\
                          .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(content)

        # JSON更新（蓄積）
        db.insert(0, {
            "title": data['radio_name'] + "さんのお悩み",
            "url": f"posts/{file_name}",
            "date": display_date,
            "description": data['description']
        })

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:2000], f, ensure_ascii=False, indent=4) # 蓄積数を2000件に増加

def main():
    if not os.path.exists(MODEL_PATH): return
    llm = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False)
    
    generated_results = []
    attempts = 0
    while len(generated_results) < GENERATE_COUNT and attempts < 60:
        res = ai_generate_letter(llm, len(generated_results))
        if res:
            generated_results.append(res)
        attempts += 1
    
    if generated_results:
        update_system(generated_results)
        print(f"完了：{len(generated_results)}件の記事を生成しました。")

if __name__ == "__main__":
    main()