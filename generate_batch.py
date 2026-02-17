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

# --- Data Pool (Matching rewrite_articles_v2.py) ---
CONCLUSIONS = [
    "今の関係に違和感があるなら、それはあなたの直感が「もっと大切にされるべき」と教えてくれているサインです。",
    "相手を変えることはできませんが、自分の「幸せの基準」を変えることは今すぐにでも可能です。",
    "孤独を恐れて自分を削るよりも、一人でも凛としていられる強さが、結果的に最高の縁を引き寄せます。",
    "どんなに好きな相手でも、あなたの尊厳を傷つけることを許してはいけません。自分を一番の味方にしてください。",
    "今の悩みは、あなたが次のステージへ進むための通過点。無理に答えを出さず、まずは自分を労わりましょう。",
    "「選ばれる」のを待つのではなく、あなたが「この人生にふさわしい相手か」を選ぶ側に立ってください。",
    "恋愛において「正解」はありません。あなたが心から納得し、笑顔でいられる道こそが唯一の正解です。",
    "失うことを恐れすぎないで。本当に必要な縁なら、一度離れても必ずまた結ばれる時が来ます。",
    "彼への愛と同じくらい、自分自身への愛を注いでください。あなたが満たされてこそ、良い関係が築けます。",
    "一歩下がる勇気を持って。俯瞰して見ることで、今まで見えなかった解決の糸口が必ず見つかります。",
    "「運命」に身を委ねるだけでなく、自分の足で一歩踏み出す勇気が、今のあなたには最も必要です。",
    "誰かの二番手で満足しないで。あなたは主役として、最高の愛を受け取る権利があります。",
    "執着を手放した瞬間に、新しい風が吹き込みます。古い殻を脱ぎ捨てるタイミングが今なのです。",
    "過去の失敗は、未来の幸せのための「授業料」にすぎません。今の自分を責めないでください。",
    "愛することは、相手を支配することではありません。お互いの自由を尊重できる関係を目指しましょう。",
    "焦って出した答えは、後悔を招くことが多いです。沈黙の時間さえも、今は大切なプロセスです。",
    "自分の価値を、他人の評価に委ねないで。あなたは今のままで、十分に愛される価値があります。",
    "「NO」と言える自分を誇りに思ってください。それは、自分自身を大切にできている証拠です。",
    "理想のパートナーを追う前に、自分が「理想の自分」に近づく努力が、最短のルートになります。",
    "感情の嵐が過ぎ去るのを待ちましょう。静かな海のような心で、次の航路を決めてください。",
    "愛されることを目的化せず、自分がどうありたいかを軸に据えましょう。自立した魅力が最大の武器です。",
    "表面的な優しさよりも、本音で向き合える誠実さを大切に。自分を偽ってまで繋ぎ止める縁に価値はありません。",
    "「いつか変わってくれる」という期待は、今の彼を否定しているのと同じ。ありのままの彼を愛せるかが鍵です。",
    "あなたの内側の充足感が、外側の現実を創ります。まずは自分を満たすことから、すべてが好転し始めます。",
    "終わりがあるからこそ、今この瞬間の輝きに意味があります。執着せず、流れに身を任せてみましょう。",
    "本当の愛は、あなたを自由にするものです。束縛や不安に縛られているなら、それは執着かもしれません。",
    "失敗してもいい、間違えてもいい。すべての経験が、あなたという人間の深みを創り上げているのですから。",
    "他人の「普通」に合わせる必要はありません。あなたにとっての幸せの形を、堂々と追求してください。",
    "どんなに夜が長くても、明けない夜はありません。今の苦しみも、いつか懐かしい思い出に変わります。",
    "自分を信じる力は、誰かに与えられるものではなく、自分の中に眠っているもの。それを呼び覚ましましょう。"
]

PSYCHOLOGIES = {
    "age-gap": [
        "年齢差があることで、相手は「自分が見守らなければ」という責任感と、「いつか飽きられるのでは」という不安を同時に抱えています。",
        "世代が違うからこそ、価値観の相違を「間違い」ではなく「発見」として楽しめる心の余裕が、彼には求められています。",
        "年上の彼は、自分の経験値を盾にプライドを守ろうとすることがあります。それは弱さの裏返しでもあります。",
        "年下の彼は、あなたに追いつこうと背伸びをしている最中かもしれません。その未熟さを包み込む包容力が鍵となります。",
        "社会的な立場や経験の差が、二人の間に見えない壁を作っているように感じる時期です。対等な対話が必要です。",
        "年齢という数字に縛られているのは彼の方かもしれません。あなたの若さや柔軟さを眩しく感じ、気後れしています。"
    ],
    "cheating": [
        "浮気に走る心理の根底には、現状への不満だけでなく、自分自身の「欠乏感」を他者で埋めようとする依存心があります。",
        "一度失った信頼を取り戻すには、言葉ではなく「継続的な行動」のみが有効です。彼はその重圧から逃げたい本音もあります。",
        "「バレなければいい」という慢心は、あなたへの甘えです。今の関係が「当たり前」になり、刺激を外に求めてしまった結果です。",
        "裏切りの背景には、親密になることへの恐怖（親密性回避）が潜んでいる場合があります。深入りを避けるための逃避です。",
        "彼はあなたの優しさに依存し、何をしても許されるという誤解をしています。明確な境界線を見せる必要があります。",
        "一時的な快楽に流される弱さは、彼自身の自尊心の低さから来ていることが多いです。外側の刺激で内側を埋めようとしています。"
    ],
    "breakup": [
        "別れた直後の男性は「自由」を謳歌しますが、日常のふとした瞬間にあなたの不在を強く意識し、後悔の波が押し寄せます。",
        "復縁を望む心理は、純粋な愛だけでなく、独占欲や執着が混ざっていることも。彼は今のあなたの「変化」を注視しています。",
        "「友達に戻ろう」という提案には、罪悪感を減らしたい、またはキープしておきたいという彼の自己中心的な心理が隠れています。",
        "思い出が美化されるまでの期間、彼は孤独と向き合っています。その空白を他の誰かで埋めようとしても、違和感を感じるはずです。",
        "別れの原因を「解決できない問題」として棚に上げ、感情だけで戻ろうとするのは危険です。彼はまだ本質を見ていません。",
        "今の彼は、あなたを失ったことで初めて「自分の一部」が欠けたような喪失感を味わっています。それが愛か執着かを見極めています。"
    ],
    "dating-app": [
        "アプリという選択肢が多い環境では、彼は「もっと良い人がいるかも」という錯覚に陥り、一人を深く知る努力を怠りがちです。",
        "プロフィールと実物のギャップに不安を感じるのはあなただけではありません。彼もまた、自分をどう見せるか必死に計算しています。",
        "メッセージの頻度が落ちるのは、関心が薄れたのではなく、単に「日常のルーチン」に組み込まれてしまった可能性もあります。",
        "「効率」を求めるあまり、心の交流が後回しになるのがアプリ恋愛の罠。彼はまだ「表面的な評価」で動いている段階です。",
        "同時進行が当たり前の世界で、彼は「比較される恐怖」を感じています。そのため、あえて深い関わりを避けようとしています。",
        "デジタルの文字だけでは伝わらない温度感があります。彼はあなたの言葉の裏にある「本気度」を測りかねている状態です。"
    ],
    "office": [
        "職場という公共の場では、彼は「男としてのメンツ」と「恋人としての役割」の間で、常に神経を尖らせています。",
        "周囲の目を気にするあまり、不器用な態度をとってしまうことも。それは彼なりにあなたと仕事を同時に守ろうとする防衛本能です。",
        "公私混同を恐れる心理が、冷たい態度として現れることがあります。彼にとって職場は「戦場」であり、私情は弱点になりえます。",
        "昇進や評価への影響を過剰に心配しているかもしれません。二人の絆がキャリアの足かせになることを最も恐れています。"
    ],
    "generic": [
        "人は「手に入りそうで入らないもの」に最も強く惹かれます。今の彼は、あなたの存在に少し甘えすぎているのかもしれません。",
        "言葉と行動が矛盾している際、信じるべきは常に「行動」です。彼の本音は、口先の説明よりも日々の振る舞いに現れています。",
        "男性は問題に直面すると「殻に閉じこもる」性質があります。放置される不安は、彼が自分を整理するための時間だと思いましょう。",
        "愛情表現の不足は、愛がないのではなく、その表現方法を知らないだけかもしれません。彼の「愛の言語」を探る時期です。",
        "今の彼は、自分自身の将来や目標に一杯いっぱいで、他者をケアする心の余白がなくなっている可能性があります。",
        "拒絶されることへの恐怖が、彼を消極的にさせている根本的な原因であることも少なくありません。安心感を求めています。",
        "沈黙を「怒り」と捉えず、「沈思」だと捉えてみてください。彼は今、言葉にならない感情の渦中にいます。",
        "無意識のうちに、彼はあなたを自分の母親や理想像に重ねているかもしれません。それは彼自身の未熟さの現れです。",
        "親密さの度合いが高まるほど、距離を取りたくなる「回避型」の愛着スタイルを持っている可能性があります。",
        "彼は今、自分に自信が持てない時期にいます。あなたの輝きが、皮肉にも彼を卑屈にさせている実情もあります。"
    ]
}

ACTIONS_POOL = [
    "日記を書いて自分の感情を客観視する",
    "一日中スマホを触らない「ネット断食」を試す",
    "今の関係を一度リセットするつもりで距離を置く",
    "あえて彼以外の新しいコミュニティに参加してみる",
    "今の悩みを紙に書き出し、優先順位をつけてみる",
    "彼に期待することを一度だけ言語化して伝える",
    "美容院やエステで、徹底的に自分を癒してあげる",
    "専門家のカウンセリングや占いで客観的な視点を得る",
    "彼との思い出に関係ない、新しい趣味を今日から始める",
    "今の素直な気持ちを「Iメッセージ」で手紙に書く",
    "信頼できる親友に、自分のダメな部分を含めて話してみる",
    "「彼がいない自分」の強みを一つ見つける",
    "彼のSNSを見ないように、短期間アカウントを停止する",
    "昔好きだった本や映画を再読・再視聴して感性を磨く",
    "部屋の模様替えをして、物理的な環境から変えてみる",
    "毎朝の瞑想を取り入れ、心の静寂（しじま）を作る",
    "「幸せのリスト」を100個書いてみる",
    "今の悩みを「10年後の自分」になったつもりで眺める",
    "一人旅を計画し、自立心を物理的に育んでみる",
    "感謝のノートを作り、毎日3つの感謝を記録する",
    "五感を意識して、今食べているものの味や空気に集中する",
    "「NO」と言う練習を、小さなことから始めてみる",
    "自分のための「聖域」となる時間や場所を確保する",
    "過去の自分に向けて、労いの言葉を書き出してみる",
    "鏡を見て、自分の一番好きな部分を一つだけ褒める",
    "運動を習慣化し、体の生命力を高めてみる",
    "靴やカバンなど、毎日使うものを丁寧に手入れする",
    "今の彼への想いを、一滴の雫に例えてイメージの中で流し去る",
    "彼に関係ない「秘密の楽しみ」を一つ持つ",
    "朝起きたらすぐに、今日一日の最高の気分を先取りして味わう"
]

NG_POOL = [
    "感情に任せて深夜に長文LINEを送ること",
    "SNSの「いいね」や足跡を過剰に追跡すること",
    "共通の友人を介して、彼の動向を執拗に探ること",
    "「私が悪いの？」と、自分を卑下して機謙を伺うこと",
    "不機嫌な態度で、相手をコントロールしようとすること",
    "過去の失敗を持ち出し、今の問題を複雑にすること",
    "「察してほしい」と無言のプレッシャーを与えること",
    "一人の時間に耐えられず、すぐに連絡をしてしまうこと",
    "占いの結果に一喜一憂し、自分の判断力を捨てること",
    "自分を犠牲にしてまで相手の理想を演じきること",
    "他の男性を当てつけに使って、彼の嫉妬を煽ること",
    "酒や衝動買いなどの一時的な快楽で心の隙間を埋めること",
    "彼との会話を勝手にSNSで公開して共感を求めること",
    "相手のプライバシーに土足で踏み入ろうとすること",
    "「別れる」と脅して、気を引こうとすること",
    "事実を確認する前に、被害妄想を膨らませて自爆すること",
    "自分の幸せを相手の行動基準に100%依存させること",
    "無理にポジティブになろうとして、負の感情に蓋をすること",
    "相手の欠点ばかりを指摘して、自分を正当化すること",
    "「もういいよ」と極端に心を閉ざして対話を拒否すること"
]

def get_yui_content(topic):
    import hashlib
    topic_lower = topic.lower()
    # Unique seed per topic to ensure uniqueness across batches
    seed = int(hashlib.sha256(topic.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    
    # Heuristic for title
    title = f"【相談】{topic}について悩んでいます…ゆい姉さんの回答"
    if "first date" in topic_lower: title = "初デートで失敗しない！彼に『また会いたい』と思わせる振る舞い"
    elif "ghosting" in topic_lower: title = "急に連絡が途絶えた…ゴースティングする男性心理と対処法"
    elif "office" in topic_lower: title = "社内恋愛の注意点！仕事と恋を両立させるためのルール"
    elif "age gap" in topic_lower: title = "年の差恋愛の悩み…ジェネレーションギャップを乗り越える方法"
    
    # Combinatorial content selection
    candidates_conc = CONCLUSIONS[:]
    rng.shuffle(candidates_conc)
    conclusion = candidates_conc[0]
    misunderstanding = candidates_conc[1]
    
    theme_key = "generic"
    if "age gap" in topic_lower: theme_key = "age-gap"
    elif "cheat" in topic_lower or "affair" in topic_lower: theme_key = "cheating"
    elif "breakup" in topic_lower or "ex" in topic_lower: theme_key = "breakup"
    elif "app" in topic_lower: theme_key = "dating-app"
    elif "office" in topic_lower: theme_key = "office"
    
    candidates_psyc = PSYCHOLOGIES[theme_key][:]
    if theme_key != "generic":
        candidates_psyc += rng.sample(PSYCHOLOGIES["generic"], 2)
    rng.shuffle(candidates_psyc)
    psychology = candidates_psyc[0]
    
    candidates_act = ACTIONS_POOL[:]
    rng.shuffle(candidates_act)
    actions = "".join([f"<li>{a}</li>" for a in candidates_act[:3]])
    
    candidates_ng = NG_POOL[:]
    rng.shuffle(candidates_ng)
    ng = "".join([f"<li>{n}</li>" for n in candidates_ng[:2]])
    
    summary_templates = [
        "今の悩みは、あなたがより輝くための試練。焦らず「{theme}」についての一歩を踏み出しましょう。",
        "「{theme}」との向き合い方は人それぞれ。正解を急がず、あなたのペースで進んでくださいね。",
        "時には立ち止まることも大切です。この「{theme}」という問題を通して、自分を再発見できるはずです。",
        "あなたは一人ではありません。この「{theme}」に悩む日々が、いつか「あってよかった」と思える日が来ます。",
        "心の声を無視しないで。今回の「{theme}」をきっかけに、本物の幸せを掴んでくださいね。",
        "「{theme}」は人生のスパイス。苦みが強い時もありますが、それが深みになります。応援しています。",
        "暗いトンネルの中にいても、必ず出口は見えます。今回の「{theme}」が、その光を見つける鍵になります。",
        "自分を信じること、それが「{theme}」を解決する唯一無二の魔法です。ゆい姉さんがついていますよ。"
    ]
    summary = rng.choice(summary_templates).format(theme=title)

    html_content = {
        "TITLE": title,
        "META_DESCRIPTION": f"{topic}についての悩みは深いですよね。ゆい姉さんが男性心理と解決策をズバリ解説します。",
        "LEAD": "恋する乙女の皆さん、こんにちは。ゆい姉さんです。今日もまた一つ、切実な悩みが届きました。一人で抱え込まず、一緒に紐解いていきましょう。",
        "QUESTION": f"最近、{topic}のことで悩んでいます。どうすればいいでしょうか？アドバイスをください。",
        "SUMMARY_ANSWER": conclusion,
        "PSYCHOLOGY": psychology,
        "ACTION_LIST": actions,
        "NG_LIST": ng,
        "MISUNDERSTANDING": misunderstanding,
        "CONCLUSION": summary,
        "RELATED": f'<li><a href="../archive.html">過去の相談を見る</a></li>'
    }
    
    return html_content, title, html_content["META_DESCRIPTION"]

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
        page_url = f"https://yui-love.vercel.app/posts/{slug}"
        
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
