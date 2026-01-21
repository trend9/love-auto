import os, json, random, re
from datetime import datetime, timedelta
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 5 

def clean_text(text):
    if not text: return ""
    text = re.sub(r'(RadioName:|Letter:|Answer:|Description:|SEOTitle:|名前:|相談:|回答:|要約:|タイトル:|結姉さん:)', '', text)
    text = re.sub(r'(\*\*|\[|\]|\*|#|<\|.*?\|>)', '', text).strip()
    return text

def ai_generate_letter(llm, theme, index):
    print(f"--- 記事 {index+1}/{GENERATE_COUNT} 生成開始: {theme} ---")
    
    prompt = f"""[人物設定: 日本人女性の結姉さん。恋愛相談に日本語で答える。]
テーマ: {theme}
RadioName: 
Letter: 
Answer: 
Description: 
SEOTitle: 
---"""

    try:
        output = llm(prompt, max_tokens=1000, temperature=0.8, stop=["---"])
        raw_text = output['choices'][0]['text'].strip()
        
        # 初期値（AIが空でもこれが出るようにする）
        res = {
            "radio_name": f"かなこ_{index}", 
            "letter": f"{theme}についての悩みです。", 
            "answer": "あなたの気持ち、よくわかるわ。今は自分を大切にして。一歩ずつ進みましょう。", 
            "description": f"{theme}に関する相談です。", 
            "seo_title": f"{theme}の悩み解決法"
        }

        # AIの回答を流し込む
        for line in raw_text.split('\n'):
            if 'RadioName:' in line: res['radio_name'] = clean_text(line.split(':', 1)[1]) or res['radio_name']
            if 'Letter:' in line: res['letter'] = clean_text(line.split(':', 1)[1]) or res['letter']
            if 'Answer:' in line: res['answer'] = clean_text(line.split(':', 1)[1]) or res['answer']
            if 'Description:' in line: res['description'] = clean_text(line.split(':', 1)[1]) or res['description']
            if 'SEOTitle:' in line: res['seo_title'] = clean_text(line.split(':', 1)[1]) or res['seo_title']

        # 英語が多すぎる場合のみ、日本語を強制注入（全滅防止）
        if len(re.findall(r'[a-zA-Z]', res['answer'])) > 50:
            res['answer'] = "ごめんなさい、うまく言葉にできないけれど、あなたの味方よ。焦らずに、まずは深呼吸してみましょうね。"

        return res
    except Exception as e:
        print(f"エラー: {e}")
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
        
        content = template.replace("{{SEO_TITLE}}", data['seo_title'])\
                          .replace("{{SEO_DESCRIPTION}}", data['description'][:100])\
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
    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)
    themes = ["復縁の悩み", "マッチングアプリの不安", "既婚者への恋", "結婚の焦り", "社内恋愛の秘密"]
    
    generated_results = []
    for i, theme in enumerate(themes[:GENERATE_COUNT]):
        res = ai_generate_letter(llm, theme, i)
        if res: generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"完了：{len(generated_results)}件の記事を生成しました。")

if __name__ == "__main__":
    main()