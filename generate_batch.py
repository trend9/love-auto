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
    topic_lower = topic.lower()
    
    # Determine the Situation (heuristic)
    situation = "恋愛"
    if "first date" in topic_lower: situation = "初デート"
    elif "office" in topic_lower: situation = "社内恋愛"
    elif "age gap" in topic_lower: situation = "年の差恋愛"
    
    title = f"【相談】{topic}について悩んでいます…ゆい姉さんの回答"
    if "first date" in topic_lower: title = "初デートで失敗しない！彼に『また会いたい』と思わせる振る舞い"
    elif "ghosting" in topic_lower: title = "急に連絡が途絶えた…ゴースティングする男性心理と対処法"
    elif "office" in topic_lower: title = "社内恋愛の注意点！仕事と恋を両立させるためのルール"
    elif "age gap" in topic_lower: title = "年の差恋愛の悩み…ジェネレーションギャップを乗り越える方法"

    desc = f"{topic}についての悩みは深いですよね。ゆい姉さんが男性心理と解決策をズバリ解説します。"
    
    # Improved Content Logics (match rewrite_articles.py)
    content = {
        "conclusion_main": "今のあなたの感情を否定せず、まずは「自分がどうしたいか」を最優先に考えましょう。",
        "psychology": "相手も今の状況に少なからず違和感や不安を感じているかもしれません。直接的な言葉を避け、行動で示している可能性があります。",
        "action": "<li>一旦距離を置いて冷静になる</li><li>自分の好きなことに没頭する時間を増やす</li><li>信頼できる友人に客観的な意見を聞く</li>",
        "ng": "<li>感情的に相手を問い詰める</li><li>SNSで相手の動向を過剰にチェックする</li>",
        "summary": f"{situation}の時期だからこそ、焦りは禁物です。「{topic}」について真剣に向き合っている自分を褒めてあげてくださいね。"
    }

    if "line" in topic_lower or "message" in topic_lower or "text" in topic_lower:
        content["conclusion_main"] = "連絡の頻度は愛情の量に比例しません。彼を待つ時間ではなく、自分を磨く時間を楽しみましょう。"
        content["psychology"] = "男性はLINEを「連絡手段」と捉えがち。既読がつくのは「確認した」という一つの完結点なのです。"
        content["action"] = "<li>自分からの連絡を一度止め、3日ほど置く</li><li>返事のいらない軽い挨拶だけにする</li><li>スマホを触らない時間を決める</li>"
        content["ng"] = "<li>長文の連打</li><li>「なんで返信ないの？」という追撃</li>"
        
    elif "cheat" in topic_lower or "affair" in topic_lower:
        content["conclusion_main"] = "あなたの尊厳を損なう相手との未来を、冷静に再考する時期です。自分を一番に守ってください。"
        content["psychology"] = "浮気には「支配欲」や「逃避」が隠れていることが多いです。あなたの責任ではなく、彼自身の問題です。"
        content["action"] = "<li>感情を抑えて事実関係を確認する</li><li>自分の今後の人生設計（自立）を見直す</li><li>境界線を明確に引く</li>"
        content["ng"] = "<li>泣き崩れて現状維持を懇願する</li><li>仕返しのために自分も過ちを犯す</li>"

    elif "breakup" in topic_lower or "ex" in topic_lower:
        content["conclusion_main"] = "復縁は「過去の修復」ではなく「新しい関係の構築」です。まずは自分を愛することから始めましょう。"
        content["psychology"] = "別れた直後は男性も混乱しています。一人の時間を過ごすことで、大切さに気づくスペースが生まれます。"
        content["action"] = "<li>冷却期間を半年設ける</li><li>新しい外見やスキルを手に入れる</li><li>彼以外の世界を広げる</li>"
        content["ng"] = "<li>「やり直したい」と何度も迫る</li><li>共通の友人に彼の近況を聞きまくる</li>"

    elif "marry" in topic_lower or "marriage" in topic_lower:
        content["conclusion_main"] = "結婚はゴールではなく、生活のスタート。価値観の「擦り合わせ」ができる相手かを見極めて。"
        content["psychology"] = "男性にとって結婚は「責任」の象徴。自由への未練と経済的な重圧を同時に感じています。"
        content["action"] = "<li>理想の生活について具体的に話し合う</li><li>彼の仕事の価値観を尊重する</li><li>二人の「共通の楽しみ」を増やす</li>"
        content["ng"] = "<li>周囲やSNSの結婚ラッシュと比較する</li><li>話し合いを感情的に切り出す</li>"

    elif "sex" in topic_lower or "libido" in topic_lower:
        content["conclusion_main"] = "性の悩みはコミュニケーションの映し鏡。恥ずかしがらず、しかし重くならずに話し合う勇気を。"
        content["psychology"] = "性的コミュニケーションにおいて、男性は「拒絶されること」を極度に恐れている場合があります。"
        content["action"] = "<li>日常的なスキンシップを増やす</li><li>「こうしてくれると嬉しい」と肯定から入る</li><li>体調やストレスを考慮し合う</li>"
        content["ng"] = "<li>相手の能力や相性を否定する</li><li>無言のまま不満を溜め込む</li>"

    html_content = {
        "TITLE": title,
        "META_DESCRIPTION": desc,
        "LEAD": "恋する乙女の皆さん、こんにちは。ゆい姉さんです。今日もまた一つ、切実な悩みが届きました。一人で抱え込まず、一緒に紐解いていきましょう。",
        "QUESTION": f"最近、{topic}のことで悩んでいます。どうすればいいでしょうか？アドバイスをください。",
        "SUMMARY_ANSWER": content["conclusion_main"],
        "PSYCHOLOGY": content["psychology"],
        "ACTION_LIST": content["action"],
        "NG_LIST": content["ng"],
        "MISUNDERSTANDING": "『愛があれば何でも伝わる』は幻想です。言葉にしなければ伝わらないこともあります。",
        "CONCLUSION": content["summary"],
        "RELATED": f'<li><a href="archive.html">過去の相談を見る</a></li>'
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
