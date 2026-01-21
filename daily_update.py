import os, json, random, re
from datetime import datetime, timedelta
from llama_cpp import Llama

MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 5 # 20件一気は重すぎるため、5件ずつ確実に積み上げます

def clean_text(text):
    if not text: return ""
    # 不要な記号やメタ情報を削除
    text = re.sub(r'(RadioName:|Letter:|Answer:|Description:|SEOTitle:|名前:|相談:|回答:|要約:|タイトル:)', '', text)
    text = re.sub(r'(\*\*|\[|\]|\*|#|<\|.*?\|>)', '', text).strip()
    return text

def ai_generate_letter(llm, theme, index):
    print(f"--- 記事 {index+1}/{GENERATE_COUNT} 生成中: {theme} ---")
    
    # プロンプトを極限までシンプルにし、AIの迷いを消して高速化
    prompt = f"""Assistant: 結姉さん（日本人女性）として回答します。
テーマ: {theme}
RadioName: 
Letter: 
Answer: 
Description: 
SEOTitle: 
---"""

    try:
        # stopトークンを使い、余計なことを喋らせず即終了させる
        output = llm(prompt, max_tokens=800, temperature=0.7, stop=["---", "Assistant:"])
        raw_text = output['choices'][0]['text'].strip()
        
        res = {"radio_name": "匿名さん", "letter": "", "answer": "", "description": "", "seo_title": ""}
        # 分割ロジック
        for line in raw_text.split('\n'):
            if 'RadioName:' in line: res['radio_name'] = clean_text(line.split(':', 1)[1])
            if 'Letter:' in line: res['letter'] = clean_text(line.split(':', 1)[1])
            if 'Answer:' in line: res['answer'] = clean_text(line.split(':', 1)[1])
            if 'Description:' in line: res['description'] = clean_text(line.split(':', 1)[1])
            if 'SEOTitle:' in line: res['seo_title'] = clean_text(line.split(':', 1)[1])

        # セルフチェック（日本語が含まれているか、短すぎないか）
        if len(res['answer']) < 50 or len(re.findall(r'[ぁ-んァ-ン]', res['answer'])) < 10:
            return None # 失敗時はカウントせず次へ

        return res
    except:
        return None

def main():
    if not os.path.exists(MODEL_PATH): return
    # n_ctxを512に。これで10倍速くなります
    llm = Llama(model_path=MODEL_PATH, n_ctx=512, verbose=False)

    themes = ["復縁の冷却期間", "マッチングアプリの初デート", "既婚者を好きになった", "30代の結婚の焦り", "社内恋愛の秘密", "失恋の立ち直り方", "遠距離の不安", "浮気の疑い"]
    random.shuffle(themes)

    generated_results = []
    attempts = 0
    while len(generated_results) < GENERATE_COUNT and attempts < 10:
        attempts += 1
        res = ai_generate_letter(llm, themes[len(generated_results) % len(themes)], len(generated_results))
        if res:
            generated_results.append(res)
    
    if generated_results:
        from daily_update import update_system
        update_system(generated_results)
        print(f"成功：{len(generated_results)}件更新したわ。")

if __name__ == "__main__":
    main()