import json
import os
import datetime
import random
import re

# --- Configuration ---
START_DATE = datetime.date(2026, 2, 14)
DAYS = 100
ARTICLES_PER_DAY = 5
IDEAS_FILE = "ideas.txt"
JSON_FILE = "data/questions.json"
POSTS_DIR = "posts"
TEMPLATE_FILE = "post_template.html"

# --- Content Generators ---
def generate_slug(topic, date_str):
    # Create a safe slug from topic
    slug = topic.lower().replace(" ", "-").replace("'", "").replace("?", "").replace("!", "")
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = f"{slug[:30]}-{date_str.replace('.', '')}" # Shorten and append date
    return f"{slug}.html"

def get_yui_content(topic):
    # Simple rule-based content generation to simulate specific advice
    # In a real scenario, this would be an LLM call, but we are batching 500 locally.
    
    topic_lower = topic.lower()
    
    title = f"【相談】{topic}について悩んでいます…ゆい姉さんの回答"
    desc = f"{topic}についての悩みは深いですよね。ゆい姉さんが男性心理と解決策をズバリ解説します。"
    
    lead = "恋する乙女の皆さん、こんにちは。ゆい姉さんです。今日もまた一つ、切実な悩みが届きました。一人で抱え込まず、一緒に紐解いていきましょう。"
    question = f"最近、{topic}のことで悩んでいます。どうすればいいでしょうか？アドバイスをください。"
    
    # Keyword logic
    if "line" in topic_lower or "message" in topic_lower or "text" in topic_lower:
        cat = "LINE・連絡"
        psychology = "男性はLINEを『連絡手段』としか見ていないことが多いです。既読スルーは『了解』のサインかもしれません。"
        action = "<li>返信を催促せず、3日は寝かせる</li><li>疑問形ばかり送らない</li><li>短文で軽やかに</li>"
        ng = "<li>長文の連打</li><li>「なんで返事くれないの？」という追撃</li>"
        summary = "連絡頻度＝愛情の量ではありません。スマホを置いて、自分の時間を楽しみましょう。"
        
    elif "date" in topic_lower:
        cat = "デート"
        psychology = "彼は『あなたを楽しませられているか』不安に思っています。女性の笑顔が一番の安心材料です。"
        action = "<li>お店の予約をしてくれたら全力で感謝</li><li>『美味しい！』『楽しい！』を言葉にする</li><li>次は自分から提案してみる</li>"
        ng = "<li>スマホばかり見る</li><li>店員さんへの態度が悪い</li>"
        summary = "デートは二人で作るもの。お客様気分でいると、彼の心は離れてしまいますよ。"
        
    elif "cheat" in topic_lower or "affair" in topic_lower:
        cat = "浮気・不倫"
        psychology = "浮気をする男性は、現状に満足していないか、単なるスリルを求めているかのどちらかです。罪悪感は薄い場合があります。"
        action = "<li>証拠を冷静に集める</li><li>感情的に問い詰めない</li><li>自分の幸せの基準を見直す</li>"
        ng = "<li>泣いてすがる</li><li>SNSで晒す</li>"
        summary = "あなたの価値を下げる相手に執着する必要はありません。自分を一番大切にしてください。"
        
    elif "breakup" in topic_lower or "ex" in topic_lower:
        cat = "復縁・失恋"
        psychology = "男性は別れた直後は解放感を感じますが、時間が経つと『名前をつけて保存』した思い出を美化し始めます。"
        action = "<li>冷却期間を置く（最低3ヶ月）</li><li>自分磨きをして変わった姿を見せる</li><li>SNSの更新を控える</li>"
        ng = "<li>酔って電話する</li><li>『友達でいいから』とすがる</li>"
        summary = "復縁のカギは『別れた原因の解消』と『変化』です。過去のあなたではなく、新しいあなたで再会しましょう。"
    
    elif "marry" in topic_lower or "marriage" in topic_lower:
        cat = "結婚"
        psychology = "男性にとって結婚は『責任』です。自由がなくなることへの恐怖と、経済的なプレッシャーを感じています。"
        action = "<li>『結婚したら楽しそう』と思わせる</li><li>彼の仕事を応援する</li><li>期限を区切って話し合う</li>"
        ng = "<li>親や周りと比較する</li><li>『ゼクシィ』を無言で置く</li>"
        summary = "結婚はゴールではなくスタート。彼が『この子となら頑張れる』と思えるパートナーを目指しましょう。"
        
    else:
        cat = "恋愛全般"
        psychology = "相手の行動には必ず『理由』があります。嫌われたと思い込む前に、相手の状況（仕事、体調）を想像してみましょう。"
        action = "<li>『I（アイ）メッセージ』で気持ちを伝える</li><li>感謝の言葉を増やす（ありがとう作戦）</li><li>笑顔を絶やさない</li>"
        ng = "<li>察してちゃんになる</li><li>不機嫌でコントロールしようとする</li>"
        summary = "恋愛の基本は自立です。彼がいなくても幸せ、彼がいるともっと幸せ。そんな女性が最強です。"

    # Translation/Ad-hoc title adjustment if topic is English key
    # Simple mapping for better titles
    if "first date" in topic_lower: title = "初デートで失敗しない！彼に『また会いたい』と思わせる振る舞い"
    elif "ghosting" in topic_lower: title = "急に連絡が途絶えた…ゴースティングする男性心理と対処法"
    elif "office" in topic_lower: title = "社内恋愛の注意点！仕事と恋を両立させるためのルール"
    elif "age gap" in topic_lower: title = "年の差恋愛の悩み…ジェネレーションギャップを乗り越える方法"
    
    html_content = {
        "TITLE": title,
        "META_DESCRIPTION": desc,
        "LEAD": lead,
        "QUESTION": question,
        "SUMMARY_ANSWER": summary,
        "PSYCHOLOGY": psychology,
        "ACTION_LIST": action,
        "NG_LIST": ng,
        "MISUNDERSTANDING": "『愛があれば何でも伝わる』は幻想です。言葉にしなければ伝わらないこともあります。",
        "CONCLUSION": f"今回のテーマ『{topic}』、いかがでしたか？悩みは成長の種。焦らず、一歩ずつ進んでいきましょう。ゆい姉さんはいつでもあなたの味方です。",
        "RELATED": f'<li><a href="archive.html">過去の相談を見る</a></li>'  # Simple link
    }
    
    return html_content, title, desc

# --- Main Process ---

# 1. Read Ideas and Template
with open(IDEAS_FILE, "r") as f:
    all_ideas = [line.strip() for line in f.readlines() if line.strip()]

with open(TEMPLATE_FILE, "r") as f:
    template_str = f.read()

# Load JSON
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r") as f:
        json_data = json.load(f)
else:
    json_data = []

new_json_entries = []
used_idea_indices = []

total_articles = DAYS * ARTICLES_PER_DAY
print(f"Generating {total_articles} articles...")

for day_offset in range(DAYS):
    current_date = START_DATE + datetime.timedelta(days=day_offset)
    date_iso = current_date.strftime("%Y-%m-%d")
    date_jp = current_date.strftime("%Y年%m月%d日")
    date_dot = current_date.strftime("%Y.%m.%d")
    
    for i in range(ARTICLES_PER_DAY):
        idea_idx = day_offset * ARTICLES_PER_DAY + i
        if idea_idx >= len(all_ideas):
            # Fallback if run out of ideas (shouldn't happen with replenish)
            topic = f"Love Advice {idea_idx}"
        else:
            topic = all_ideas[idea_idx]
            used_idea_indices.append(idea_idx)
            
        slug = generate_slug(topic, date_dot)
        file_path = os.path.join(POSTS_DIR, slug)
        page_url = f"https://trend9.github.io/love-auto/posts/{slug}"
        
        content_map, title, desc = get_yui_content(topic)
        
        # Fill Template
        html = template_str
        html = html.replace("{{TITLE}}", title)
        html = html.replace("{{META_DESCRIPTION}}", desc)
        html = html.replace("{{DATE_ISO}}", date_iso)
        html = html.replace("{{DATE_JP}}", date_jp)
        html = html.replace("{{PAGE_URL}}", page_url)
        html = html.replace("{{LEAD}}", content_map["LEAD"])
        html = html.replace("{{QUESTION}}", content_map["QUESTION"])
        html = html.replace("{{SUMMARY_ANSWER}}", content_map["SUMMARY_ANSWER"])
        html = html.replace("{{PSYCHOLOGY}}", content_map["PSYCHOLOGY"])
        html = html.replace("{{ACTION_LIST}}", content_map["ACTION_LIST"])
        html = html.replace("{{NG_LIST}}", content_map["NG_LIST"])
        html = html.replace("{{MISUNDERSTANDING}}", content_map["MISUNDERSTANDING"])
        html = html.replace("{{CONCLUSION}}", content_map["CONCLUSION"])
        # Simple placeholder replacements for others
        html = html.replace("{{CANONICAL}}", f'<link rel="canonical" href="{page_url}">')
        html = html.replace("{{FAQ}}", "") # Skip complex schema for batch
        html = html.replace("{{RELATED}}", content_map["RELATED"])
        html = html.replace("{{PREV}}", "")
        html = html.replace("{{NEXT}}", "")
        
        # Inject CSS (Requirement)
        if '<link rel="stylesheet" href="../style.css">' in html:
            html = html.replace('<link rel="stylesheet" href="../style.css">', 
                                '<link rel="stylesheet" href="../style.css">\n  <link rel="stylesheet" href="post-style.css">')
        
        # Write File
        with open(file_path, "w") as f:
            f.write(html)
            
        # Add to JSON list (prepend logic handled later or just collect)
        new_json_entries.append({
            "title": title,
            "description": desc,
            "date": date_dot,
            "url": f"posts/{slug}"
        })

# Prepend new entries to JSON
# Reverse new_entries so that the latest date (day 100) is first at top? 
# Usually newer dates are at top. 
# Loop was Day 0 -> Day 99. 
# So Day 0 is "tomorrow". Day 99 is future.
# If we prepend them in order [Day 0...Day 99], Day 0 will be at top? 
# No, if we prepend [1, 2, 3], result is [3, 2, 1, old].
# We want [Day 99 ... Day 0, old].
# So we should append to new_json_entries in chronological order, then reverse before prepending.
new_json_entries.reverse() 
final_json = new_json_entries + json_data

with open(JSON_FILE, "w") as f:
    json.dump(final_json, f, indent=4, ensure_ascii=False)

# Remove used ideas
# Sort used indices desc to delete safely
used_idea_indices.sort(reverse=True)
remaining_ideas = all_ideas[:] 
# Actually easier to just slice
remaining_ideas = all_ideas[len(used_idea_indices):]

with open(IDEAS_FILE, "w") as f:
    f.writelines([line + "\n" for line in remaining_ideas])

print("Batch generation complete.")
