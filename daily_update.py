import os, json, random, re
from datetime import datetime, timedelta
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 5 

def clean_text(text):
    if not text: return ""
    # 不要なプレフィックスや記号を徹底削除
    text = re.sub(r'(名前:|相談:|回答:|要約:|タイトル:|RadioName:|Letter:|Answer:|Description:|SEOTitle:|結姉さん:)', '', text)
    text = re.sub(r'(\*\*|\[|\]|\*|#|<\|.*?\|>)', '', text).strip()
    return text

def ai_generate_letter(llm, theme, index):
    print(f"--- 記事 {index+1}/{GENERATE_COUNT} 生成開始: {theme} ---")
    
    # ご提案の「AIが理解しやすいシンプルな指示」を構成
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは30代前半の日本人女性「結姉さん」です。以下の4点を日本語で作成してください。
1.名前: 日本人女性の名前
2.タイトル: 恋愛相談掲示板にありそうな簡潔なタイトル
3.相談: テーマ「{theme}」に基づいた具体的な悩み
4.回答: 寄り添いながら解決へ導く100文字前後のアドバイス
5.要約: 相談と回答を簡潔にまとめた文
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
1.名前:"""

    try:
        # n_ctxを512に絞り、生成に集中させる
        output = llm(prompt, max_tokens=1000, temperature=0.8, stop=["<|eot_id|>"])
        raw_text = "1.名前:" + output['choices'][0]['text'].strip()
        
        # デフォルト値を設定
        res = {"radio_name": f"かなこ_{index}", "letter": "", "answer": "", "description": "", "seo_title": ""}

        # より確実な分割（1. 2. などの数字を目印にする）
        lines = raw_text.split('\n')
        for line in lines:
            if '1.名前:' in line: res['radio_name'] = clean_text(line.split(':', 1)[1])
            if '2.タイトル:' in line: res['seo_title'] = clean_text(line.split(':', 1)[1])
            if '3.相談:' in line: res['letter'] = clean_text(line.split(':', 1)[1])
            if '4.回答:' in line: res['answer'] = clean_text(line.split(':', 1)[1])
            if '5.要約:' in line: res['description'] = clean_text(line.split(':', 1)[1])

        # 最終チェック：もしAIがタイトルや回答を書き漏らした時だけテーマから補完
        if len(res['seo_title']) < 3: res['seo_title'] = f"{theme}についての悩み相談"
        if len(res['letter']) < 10: res['letter'] = f"{theme}のことで悩んでいます。どうすればいいでしょうか。"
        if len(res['answer']) < 10: res['answer'] = "あなたの気持ち、よくわかるわ。まずはゆっくり深呼吸して、自分を大切にしてね。"
        if len(res['description']) < 5: res['description'] = res['letter'][:50]

        return res
    except Exception as e:
        print(f"エラー: {e}")
        return None

# update_system関数とmain関数は前回のものをそのまま利用
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
    random.shuffle(themes)
    
    generated_results = []
    for i, theme in enumerate(themes[:GENERATE_COUNT]):
        res = ai_generate_letter(llm, theme, i)
        if res: generated_results.append(res)
    
    if generated_results:
        update_system(generated_results)
        print(f"完了：{len(generated_results)}件の記事を生成しました。")

if __name__ == "__main__":
    main()