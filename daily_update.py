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
    
    themes = ["片思いの切なさ", "復縁の可能性", "不倫や浮気の悩み", "遠距離恋愛の寂しさ", "結婚への焦り", "マッチングアプリの出会い", "社内恋愛の秘密", "倦怠期の乗り越え方", "失恋の傷跡", "嫉妬心との付き合い方"]
    theme = random.choice(themes)

    try:
        # Llama-3の構造に合わせた、日本語強制プロンプト
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは日本の女性「結姉さん（ゆいねえさん）」です。
【重要：日本語以外の言語は禁止】
・回答はすべて、美しく自然な「日本語」のみで行ってください。
・英語、中国語は一文字も出力してはいけません。
・RadioName, Letter, Answer, Description の4項目を必ず作成してください。
・アスタリスク(*)やカッコ[]、記号は一切使わないでください。<|eot_id|><|start_header_id|>user<|end_header_id|>
テーマ「{theme}」でお悩み相談を作成してください。日本語のみでお願いします。<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RadioName:"""

        output = llm(prompt, max_tokens=1200, temperature=0.8, stop=["<|eot_id|>", "---"])
        full_text = "RadioName:" + output['choices'][0]['text'].strip()
        
        res = {}
        for line in full_text.split('\n'):
            # 記号の徹底除去
            line = line.replace('*', '').replace('[', '').replace(']', '').replace('#', '').strip()
            if 'RadioName:' in line: res['radio_name'] = line.split(':', 1)[1].strip()
            if 'Letter:' in line: res['letter'] = line.split(':', 1)[1].strip()
            if 'Answer:' in line: res['answer'] = line.split(':', 1)[1].strip()
            if 'Description:' in line: res['description'] = line.split(':', 1)[1].strip()
        
        # --- 検閲ロジック ---
        # 1. 4項目揃っているか
        if len(res) < 4: return None
        
        # 2. 英語混入チェック (アルファベットが10文字以上あれば英語とみなし破棄)
        eng_chars = re.findall(r'[a-zA-Z]', res.get('answer', ''))
        if len(eng_chars) > 10:
            print(f"【検閲】英語の混入を検知したため、再生成します。")
            return None
        
        # 3. テンプレート文字の残存チェック
        if "例:" in str(res.values()) or "考案" in str(res.values()):
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

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    
    for i, data in enumerate(new_data_list):
        time_suffix = (now + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        display_date = now.strftime("%Y/%m/%d %H:%M")
        file_name = f"{time_suffix}.html"
        
        content = template.replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", data['letter'])\
                          .replace("{{ANSWER}}", data['answer'])\
                          .replace("{{DESCRIPTION}}", data['description'])\
                          .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(content)

        db.insert(0, {
            "title": data['radio_name'] + "さんのお悩み",
            "url": f"posts/{file_name}",
            "date": display_date,
            "description": data['description']
        })

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:1000], f, ensure_ascii=False, indent=4)

def main():
    if not os.path.exists(MODEL_PATH): return
    llm = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False)
    
    generated_results = []
    attempts = 0
    # 20件揃うまで粘る（最大50回試行）
    while len(generated_results) < GENERATE_COUNT and attempts < 50:
        res = ai_generate_letter(llm, len(generated_results))
        if res:
            generated_results.append(res)
        attempts += 1
    
    if generated_results:
        update_system(generated_results)
        print(f"完了：{len(generated_results)}件のピュアな日本語記事を生成したわ。")

if __name__ == "__main__":
    main()