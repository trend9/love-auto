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
    themes = [
        "既婚者の彼を諦める方法", "マッチングアプリで2回目に誘われない理由", 
        "片思いのLINE頻度", "30代独身の結婚への焦り", 
        "復縁の可能性と冷却期間", "社内恋愛がバレるリスク",
        "元カレへの未練を断ち切る", "マッチングアプリの初対面の会話"
    ]
    theme = random.choice(themes)

    try:
        # 指示語を日本語に統一し、英語の入り込む余地を消す
        prompt = f"""[System: あなたは包容力のある日本の女性、結姉さんです。必ず日本語のみで、記号を使わずに回答してください。]
テーマ: {theme}
名前: 
相談: 結姉さん、聞いて…
回答: 
要約: 
タイトル: 
---"""
        output = llm(prompt, max_tokens=1000, temperature=0.7, stop=["---"])
        text = output['choices'][0]['text'].strip()
        
        # データの抽出ロジック（正規表現でより確実に）
        res = {"radio_name": f"匿名さん_{index+1}", "letter": "", "answer": "", "description": "", "seo_title": ""}
        
        parts = {
            "name": r"名前:(.*?)(\n|$)",
            "letter": r"相談:(.*?)(\n回答:|\n要約:|\nタイトル:|$)",
            "answer": r"回答:(.*?)(\n要約:|\nタイトル:|$)",
            "description": r"要約:(.*?)(\nタイトル:|$)",
            "title": r"タイトル:(.*?)$"
        }

        for key, pattern in parts.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                val = match.group(1).replace('*', '').replace('[', '').replace(']', '').strip()
                if key == "name": res["radio_name"] = val or res["radio_name"]
                elif key == "letter": res["letter"] = val
                elif key == "answer": res["answer"] = val
                elif key == "description": res["description"] = val
                elif key == "title": res["seo_title"] = val

        # --- 最終防衛策（データが空、または英語の場合） ---
        if not res["letter"] or len(re.findall(r'[a-zA-Z]', res["letter"])) > 20:
            res["letter"] = f"結姉さん、聞いて。{theme}のことで悩んでいるんです。どうすればいいか分からなくて…"
        
        if not res["answer"] or len(re.findall(r'[a-zA-Z]', res["answer"])) > 20:
            res["answer"] = "あなたの悩み、しっかり受け止めたわ。今は無理をせず、自分の心を一番に大切にしてあげて。一歩ずつ、一緒に考えていきましょうね。"

        if not res["seo_title"] or len(res["seo_title"]) < 5:
            res["seo_title"] = f"「{theme}」のお悩み相談。結姉さんが答える解決へのヒント"

        if not res["description"]:
            res["description"] = res["letter"][:80] + "..."

        return res
    except Exception as e:
        print(f"エラー発生: {e}")
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
        
        # 変数置換（テンプレート側のキーと一致させる）
        content = template.replace("{{SEO_TITLE}}", data['seo_title'])\
                          .replace("{{SEO_DESCRIPTION}}", data['description'])\
                          .replace("{{TITLE}}", data['radio_name'] + "さんからのお便り")\
                          .replace("{{LETTER}}", data['letter'])\
                          .replace("{{ANSWER}}", data['answer'])\
                          .replace("{{DATE}}", display_date)
        
        with open(f"posts/{file_name}", "w", encoding="utf-8") as f:
            f.write(content)

        db.insert(0, {
            "title": data['seo_title'],
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
    for i in range(GENERATE_COUNT):
        res = ai_generate_letter(llm, i)
        if res:
            generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"完了：{len(generated_results)}件更新したわ。")

if __name__ == "__main__":
    main()