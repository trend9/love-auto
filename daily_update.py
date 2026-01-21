import os
import json
import shutil
import random
from datetime import datetime, timedelta
from llama_cpp import Llama

# 設定
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 20

def ai_generate_letter(llm, index):
    print(f"結姉さんが{index+1}通目のお便りを執筆中...")
    
    themes = ["片思い", "復縁", "不倫・浮気", "遠距離恋愛", "結婚の悩み", "マッチングアプリ", "社内恋愛", "倦怠期", "失恋", "嫉妬"]
    theme = random.choice(themes)

    try:
        # プロンプトを「例」を見せる形式に変更（One-shotプロンプティング）
        prompt = f"""[System: あなたは包容力のある日本の女性「結姉さん」です。]
恋愛テーマ: {theme}
以下の項目を日本語で埋めてください。[]などの記号は出力しないでください。

RadioName: (例: 桜んぼ)
Letter: (例: 結姉さん、聞いて。彼が最近冷たくて...)
Answer: (例: それは不安になるわね。でも、今は自分の時間を大切にしてみて...)
Description: (例: 彼との関係に悩む女性へ、結姉さんからのアドバイス。)

---
RadioName:"""

        # 確実に文章を作らせるためにmax_tokensを調整
        output = llm(prompt, max_tokens=1000, temperature=0.8, stop=["---"])
        text = "RadioName:" + output['choices'][0]['text'].strip()
        
        res = {}
        # 改良されたパースロジック
        lines = text.split('\n')
        for line in lines:
            if 'RadioName:' in line: res['radio_name'] = line.replace('RadioName:', '').replace('[', '').replace(']', '').strip()
            if 'Letter:' in line: res['letter'] = line.replace('Letter:', '').replace('[', '').replace(']', '').strip()
            if 'Answer:' in line: res['answer'] = line.replace('Answer:', '').replace('[', '').replace(']', '').strip()
            if 'Description:' in line: res['description'] = line.replace('Description:', '').replace('[', '').replace(']', '').strip()
        
        # 記号がそのまま残っていたり、空だったりする場合の最終防衛策
        if not res.get('letter') or "お悩み文章" in str(res.get('letter')):
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
        print("モデルがないわよ。")
        return

    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)
    
    generated_results = []
    for i in range(GENERATE_COUNT):
        res = ai_generate_letter(llm, i)
        if res:
            generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"合計{len(generated_results)}件のお悩みを生成したわ！")
    else:
        print("1件も生成できなかったみたい...")

if __name__ == "__main__":
    main()