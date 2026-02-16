#!/usr/bin/env python3
"""
全ての記事HTMLファイルにnote-embed.jsへの参照を追加するスクリプト
"""
import os
import re
from pathlib import Path

def add_note_embed_script(html_file_path):
    """HTMLファイルにnote-embed.jsへのスクリプトタグを追加"""
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 既にスクリプトタグが存在する場合はスキップ
    if 'note-embed.js' in content:
        return False
    
    # </body>の直前にスクリプトタグを挿入
    script_tag = '  <script src="note-embed.js"></script>\n</body>'
    
    if '</body>' in content:
        content = content.replace('</body>', script_tag)
        
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    posts_dir = Path(__file__).parent / 'posts'
    
    if not posts_dir.exists():
        print(f"Error: {posts_dir} が見つかりません")
        return
    
    html_files = list(posts_dir.glob('*.html'))
    total = len(html_files)
    updated = 0
    
    print(f"処理開始: {total}個のHTMLファイルを確認中...")
    
    for html_file in html_files:
        if add_note_embed_script(html_file):
            updated += 1
            if updated % 50 == 0:
                print(f"進捗: {updated}/{total} 完了")
    
    print(f"\n完了!")
    print(f"更新: {updated}ファイル")
    print(f"スキップ: {total - updated}ファイル (既に追加済み)")

if __name__ == '__main__':
    main()
