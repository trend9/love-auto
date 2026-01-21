import os
import json
import random
import re
from datetime import datetime, timedelta
from llama_cpp import Llama

# 設定
MODEL_PATH = "./models/model.gguf"
GENERATE_COUNT = 20

def clean_text(text):
    """不要な記号、システム文、英語のメタ指示を完全に削除"""
    if not text: return ""
    text = re.sub(r'(RadioName:|Letter:|Answer:|Description:|SEOTitle:|名前:|相談:|回答:|要約:|タイトル:)', '', text)
    text = re.sub(r'(\*\*|\[|\]|\*|#)', '', text).strip()
    # 英語のシステム指示行を削除
    lines = [line for line in text.split('\n') if not re.search(r'(please proceed|next question|instruction|system:|assistant:)', line, re.I)]
    return "\n".join(lines).strip()

def ai_generate_letter(llm, specific_theme, index):
    print(f"--- 記事 {index+1}/20 の生成を開始 ---")
    
    attempts = 0
    while attempts < 5:
        attempts += 1
        try:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
あなたは日本の優しい女性「結姉さん」です。以下の恋愛相談を作成してください。
【禁止事項】英語、システム指示、記号（**など）、定型文の使い回し。
【必須】相談者の悩みに対し、寄り添いながらも具体的な解決へ導く400文字以上の温かい回答。

出力形式:
RadioName: (日本人女性らしい名前)
Letter: (具体的なお悩み内容)
Answer: (結姉さんからの解決へ導く回答)
Description: (SEO用の要約)
SEOTitle: (検索されやすいタイトル)
<|eot_id|><|start_header_id|>user<|end_header_id|>
今回のテーマ: {specific_theme}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RadioName:"""

            output = llm(prompt, max_tokens=1500, temperature=0.8, stop=["<|eot_id|>"])
            raw_text = "RadioName:" + output['choices'][0]['text'].strip()
            
            # パース処理
            res = {"radio_name": "", "letter": "", "answer": "", "description": "", "seo_title": ""}
            sections = re.split(r'(RadioName:|Letter:|Answer:|Description:|SEOTitle:)', raw_text)
            for i in range(1, len(sections), 2):
                key, val = sections[i], clean_text(sections[i+1])
                if "RadioName:" in key: res["radio_name"] = val
                elif "Letter:" in key: res["letter"] = val
                elif "Answer:" in key: res["answer"] = val
                elif "Description:" in key: res["description"] = val
                elif "SEOTitle:" in key: res["seo_title"] = val

            # --- セルフチェック機能 ---
            is_valid = True
            error_msg = ""

            # 1. 英語混入チェック
            if len(re.findall(r'[a-zA-Z]', res["answer"])) > 20:
                is_valid = False; error_msg = "英語混入"
            
            # 2. 回答の長さチェック（短すぎるとボツ）
            if len(res["answer"]) < 100:
                is_valid = False; error_msg = "回答不足"

            # 3. ラジオネームが不適切（テーマ名や記号）
            forbidden_names = ["恋愛", "相談", "不倫", "結婚", "テーマ", "匿名"]
            if any(f in res["radio_name"] for f in forbidden_names) or not res["radio_name"]:
                res["radio_name"] = random.choice(["さくら", "美咲", "ななみ", "ゆいな", "加奈", "まどか"])

            # 4. タイトルの妥当性
            if len(res["seo_title"]) < 10 or "SEOTitle" in res["seo_title"]:
                is_valid = False; error_msg = "タイトル不備"

            if is_valid:
                print(f"  -> チェック合格 (試行回数: {attempts})")
                return res
            else:
                print(f"  -> チェック不合格 ({error_msg})。再試行します...")

        except Exception as e:
            print(f"  -> エラー発生: {e}")
    
    return None

def main():
    if not os.path.exists(MODEL_PATH): return
    llm = Llama(model_path=MODEL_PATH, n_ctx=2048, verbose=False)

    # 20個の重複しないテーマを作成
    all_themes = [
        "マッチングアプリで会った後の未読無視", "職場の既婚男性への片思い", "同棲中の彼氏の浮気疑惑",
        "元カレとの復縁を望む冷却期間", "親に反対されている結婚", "婚活疲れと自信喪失",
        "社内恋愛がバレた時の対処法", "遠距離恋愛のマンネリ解消", "元カノと連絡を取る彼氏への嫉妬",
        "30代後半の独身の焦りと不安", "マッチングアプリでの初デートの沈黙", "浮気相手からの卒業",
        "彼氏の束縛が激しい悩み", "好きだけど価値観が合わない別れ", "年の差恋愛の悩み",
        "友達以上恋人未満の期間が長い", "マッチングアプリのプロフィールの嘘", "結婚直前のマリッジブルー",
        "不倫関係を綺麗に清算する方法", "失恋から立ち直るための心の整理"
    ]
    random.shuffle(all_themes)
    selected_themes = all_themes[:GENERATE_COUNT]

    generated_results = []
    for i, theme in enumerate(selected_themes):
        res = ai_generate_letter(llm, theme, i)
        if res:
            generated_results.append(res)
    
    if generated_results:
        # JSON更新とHTML生成（update_system関数は以前のものを利用、適宜統合）
        from daily_update import update_system # もしくは同ファイル内に配置
        update_system(generated_results)
        print(f"完了：全{len(generated_results)}件の精密チェック済み記事を生成しました。")

if __name__ == "__main__":
    main()