import os
import json
import shutil
import random
from datetime import datetime, timedelta
from llama_cpp import Llama

# 設定
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 20  # 1回の実行で生成する件数

def ai_generate_letter(llm, index):
    print(f"結姉さんが{index+1}通目のお便りを執筆中...")
    
    # 毎回バリエーションが出るようにテーマをランダムに提示
    themes = ["片思い", "復縁", "不倫・浮気", "遠距離恋愛", "結婚の悩み", "マッチングアプリ", "社内恋愛", "倦怠期"]
    theme = random.choice(themes)

    try:
        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。]
お題: {theme}に関する恋愛の悩み。
以下の形式で、一人の女性からの切ないお便りと、それに対するあなたの回答を書いてください。日本語のみ。

RadioName: [可愛い名前]
Letter: [結姉さん、聞いて…で始まるお悩み文章]
Answer: [結姉さんの優しくも芯のある回答]
Description: [100文字程度の要約]"""

        output = llm(prompt, max_tokens=1000, temperature=0.8)
        text = output['choices'][0]['text'].strip()
        
        res = {}
        for line in text.split('\n'):
            if 'RadioName:' in line: res['radio_name'] = line.split(':', 1)[1].strip()
            if 'Letter:' in line: res['letter'] = line.split(':', 1)[1].strip()
            if 'Answer:' in line: res['answer'] = line.split(':', 1)[1].strip()
            if 'Description:' in line: res['description'] = line.split(':', 1)[1].strip()
        
        # 最低限のバリデーション
        if len(res) < 4: return None
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
        # 1秒ずつずらしてファイル名をユニークにする
        time_suffix = (now + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        display_date = now.strftime("%Y/%m/%d")
        file_name = f"{time_suffix}.html"
        
        # HTML生成
        content = template.replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", data['letter'])\
                          .replace("{{ANSWER}}", data['answer'])\
                          .replace("{{DESCRIPTION}}", data['description'])\
                          .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(content)

        # JSONへ追加
        db.insert(0, {
            "title": data['radio_name'] + "さんのお悩み",
            "url": f"posts/{file_name}",
            "date": display_date,
            "description": data['description']
        })

    # 最大500件保持
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:500], f, ensure_ascii=False, indent=4)

def main():
    if not os.path.exists(MODEL_PATH):
        print("モデルが見つからないわ。")
        return

    # メモリ節約のため一回だけロード
    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)
    
    generated_results = []
    for i in range(GENERATE_COUNT):
        res = ai_generate_letter(llm, i)
        if res:
            generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"合計{len(generated_results)}件のお悩みを生成したわ！")

if __name__ == "__main__":
    main()