import os
import re

posts_dir = 'posts'

# 標準的なサイドバー構造（左・右）とラッパー
sidebar_left_html = """  <div class="site-wrapper">
    <aside class="sidebar-left">
      <div class="yui-word"><strong>ゆい姉さん今日の一言</strong><br><span id="daily-msg">読み込み中...</span></div>
      <button class="omikuji-btn" onclick="drawOmikuji()">ゆい姉さんおみくじ</button>
      <div id="omikuji-result"
        style="margin-top:10px; font-size:0.85rem; color:#d63384; text-align:center; font-weight:bold;"></div>
      <div class="ad-container">
        <!-- 広告1 -->
        <div class="ad-space">
          <a href="https://px.a8.net/svt/ejp?a8mat=3T8ZHQ+8NDQ5U+22QA+HZXM9" rel="nofollow">
            <img border="0" height="250" alt=""
              src="https://www21.a8.net/svt/bgt?aid=230526638523&wid=001&eno=01&mid=s00000009685003023000&mc=1"></a>
          <img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=3T8ZHQ+8NDQ5U+22QA+HZXM9" alt="">
        </div>
        <!-- 広告2 -->
        <div class="ad-space">
          <a href="https://px.a8.net/svt/ejp?a8mat=3T909J+7N2A9E+9FQ+6DRLT" rel="nofollow">
            <img border="0" height="250" alt=""
              src="https://www26.a8.net/svt/bgt?aid=230527639462&wid=001&eno=01&mid=s00000001223001072000&mc=1"></a>
          <img border="0" width="1" height="1" src="https://www13.a8.net/0.gif?a8mat=3T909J+7N2A9E+9FQ+6DRLT" alt="">
        </div>
      </div>
    </aside>"""

sidebar_right_html = """    <!-- モバイル用広告エリア（ページ下部） -->
    <div class="mobile-ad-area">
      <!-- 広告1 -->
      <div class="ad-space">
        <a href="https://px.a8.net/svt/ejp?a8mat=3T8ZHQ+8NDQ5U+22QA+HZXM9" rel="nofollow">
          <img border="0" height="250" alt=""
            src="https://www21.a8.net/svt/bgt?aid=230526638523&wid=001&eno=01&mid=s00000009685003023000&mc=1"></a>
        <img border="0" width="1" height="1" src="https://www11.a8.net/0.gif?a8mat=3T8ZHQ+8NDQ5U+22QA+HZXM9" alt="">
      </div>
      <!-- 広告2 -->
      <div class="ad-space">
        <a href="https://px.a8.net/svt/ejp?a8mat=3T909J+7N2A9E+9FQ+6DRLT" rel="nofollow">
          <img border="0" height="250" alt=""
            src="https://www26.a8.net/svt/bgt?aid=230527639462&wid=001&eno=01&mid=s00000001223001072000&mc=1"></a>
        <img border="0" width="1" height="1" src="https://www13.a8.net/0.gif?a8mat=3T909J+7N2A9E+9FQ+6DRLT" alt="">
      </div>
    </div>

    <aside class="sidebar-right">
      <div class="note-box">
        <iframe src="https://note.com/embed/notes/nea7132e15dbe"
          style="border: 0; display: block; max-width: 100%; width: 100%; padding: 0px; margin: 10px 0; position: static; visibility: visible;"
          height="400"></iframe>
      </div>
      <a href="../profile.html" class="bubble">ゆい姉さんのプロフィール</a>
      <img src="../yui.png" alt="ゆい姉さん" class="yui-img">
    </aside>
  </div>"""

script_logic = """  <script>
    // おみくじと今日の一言のロジック
    const words = ["自分を大切にね。", "明日はきっといい日になるわ。", "あなたの味方はここにいるわ。"];
    if (document.getElementById('daily-msg')) {
      document.getElementById('daily-msg').innerText = words[Math.floor(Math.random() * words.length)];
    }

    function drawOmikuji() {
      const res = ["大吉：最高の出会いがあるかも！", "中吉：自分磨きが吉。", "吉：幸せが見つかる予感。"];
      if (document.getElementById('omikuji-result')) {
        document.getElementById('omikuji-result').innerText = res[Math.floor(Math.random() * res.length)];
      }
    }
  </script>"""

count = 0
for filename in os.listdir(posts_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(posts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 既に適用済みかチェック
        if 'class="site-wrapper"' in content:
            continue
            
        # 1. <body> の直後に sidebar_left を挿入
        content = re.sub(r'<body>', '<body>\n' + sidebar_left_html, content)
        
        # 2. </body> の直前に sidebar_right と script_logic を挿入
        # 既存の note-embed.js があればその手前に
        if '<script src="note-embed.js"></script>' in content:
            replacement = sidebar_right_html + '\n\n' + script_logic + '\n  <script src="note-embed.js"></script>'
            content = re.sub(r'<script src="note-embed.js"></script>', replacement, content)
        else:
            content = re.sub(r'</body>', sidebar_right_html + '\n\n' + script_logic + '\n</body>', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"Updated {count} posts.")
