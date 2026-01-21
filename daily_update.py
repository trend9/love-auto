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
    themes = ["片思い", "復縁", "不倫・浮気", "遠距離恋愛", "結婚", "マッチングアプリ", "社内恋愛", "倦怠期", "失恋", "嫉妬"]
    theme = random.choice(themes)

    try:
        # 日本語での出力を絶対命令
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは包容力のある日本の女性「結姉さん」です。必ず全て日本語で回答してください。英語と中国語は禁止です。
以下の4つの項目を作成してください。カッコや記号、アスタリスク(*)は一切使わないでください。

RadioName: 相談者の可愛い名前
Letter: 結姉さん、聞いて…で始まる日本語の悩み相談（300文字程度）
Answer: 結姉さんからの優しく芯のある日本語の回答（300文字程度）
Description: お悩みの日本語要約（50文字程度）<|eot_id|><|start_header_id|>user<|end_header_id|>
テーマは「{theme}」です。日本語で作成してください。<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RadioName:"""

        output = llm(prompt, max_tokens=1000, temperature=0.8, stop=["<|eot_id|>"])
        full_text = "RadioName:" + output['choices'][0]['text'].strip()
        
        res = {}
        # 頑丈なパース処理（不要な記号や英語を徹底除去）
        for line in full_text.split('\n'):
            line = line.replace('*', '').replace('[', '').replace(']', '').strip()
            if 'RadioName:' in line: res['radio_name'] = line.split(':', 1)[1].strip()
            if 'Letter:' in line: res['letter'] = line.split(':', 1)[1].strip()
            if 'Answer:' in line: res['answer'] = line.split(':', 1)[1].strip()
            if 'Description:' in line: res['description'] = line.split(':', 1)[1].strip()
        
        # 英語が混じっていたらボツにする（簡易判定）
        if any(char.isalpha() for char in res.get('answer', 'abc')[:10] if char.isascii()):
            # 英語（アルファベット）が多ければ失敗とみなす
            return None
            
        return res if len(res) >= 4 else None
    except:
        return None

def update_system(new_data_list):
    os.makedirs("posts", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    db_path = "data/questions.json"
    db = []
    # 過去のデータを読み込む（蓄積させるため）
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = []

    with open("post_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    now = datetime.now()
    
    for i, data in enumerate(new_data_list):
        # 1件ごとにユニークなファイル名（秒単位）
        time_suffix = (now + timedelta(seconds=i)).strftime("%Y%m%d_%H%M%S")
        display_date = now.strftime("%Y/%m/%d %H:%M")
        file_name = f"{time_suffix}.html"
        
        html_content = template.replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                              .replace("{{LETTER}}", data['letter'])\
                              .replace("{{ANSWER}}", data['answer'])\
                              .replace("{{DESCRIPTION}}", data['description'])\
                              .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(html_content)

        # 常に先頭に追加（新しい順）
        db.insert(0, {
            "title": data['radio_name'] + "さんのお悩み",
            "url": f"posts/{file_name}",
            "date": display_date,
            "description": data['description']
        })

    # 最大1000件まで蓄積して保存
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db[:1000], f, ensure_ascii=False, indent=4)

def main():
    if not os.path.exists(MODEL_PATH): return
    llm = Llama(model_path=MODEL_PATH, n_ctx=1024, verbose=False)
    
    generated_results = []
    # 20件生成できるまでループ（最大40回試行）
    attempts = 0
    while len(generated_results) < GENERATE_COUNT and attempts < 40:
        res = ai_generate_letter(llm, len(generated_results))
        if res:
            generated_results.append(res)
        attempts += 1
    
    if generated_results:
        update_system(generated_results)
        print(f"成功！{len(generated_results)}件更新したわ。")

if __name__ == "__main__":
    main()