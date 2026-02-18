#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全HTMLファイルから不適切なURL（日本語や特殊文字を含む）を検出し、
実際のファイル名に基づいて正しいURLに修正するスクリプト（改善版）
"""

import os
import re
from pathlib import Path
from urllib.parse import quote, unquote

# 対象ディレクトリ
POSTS_DIR = "posts"
BASE_URL = "https://yui-love.vercel.app/posts/"

def get_actual_filename_map():
    """postsディレクトリ内の実際のHTMLファイル名をマッピング"""
    posts_path = Path(POSTS_DIR)
    actual_files = {}
    
    for html_file in posts_path.glob("*.html"):
        filename = html_file.name
        # ファイル名をキーとして保存
        actual_files[filename] = filename
        # URLエンコードされた形もキーに追加
        encoded = quote(filename, safe='')
        actual_files[encoded] = filename
        
    return actual_files

def extract_filename_from_url(url):
    """URLからファイル名部分を抽出"""
    # https://yui-love.vercel.app/posts/xxxxx.html から xxxxx.html を取得
    match = re.search(r'/posts/([^"]+\.html)', url)
    if match:
        return match.group(1)
    return None

def find_correct_filename(incorrect_filename, actual_files, current_file=None):
    """
    不適切なファイル名から正しいファイル名を推測
    現在のファイル名をコンテキストとして使用
    """
    # URLデコード
    decoded = unquote(incorrect_filename)
    
    # 既に正しいファイル名の場合
    if decoded in actual_files:
        return actual_files[decoded]
    
    # 現在のファイル自身を指している可能性をチェック
    if current_file and current_file in actual_files.values():
        # ファイル名から日付を抽出
        current_date = re.search(r'(\d{8})', current_file)
        incorrect_date = re.search(r'(\d{8})', decoded)
        
        if current_date and incorrect_date and current_date.group(1) == incorrect_date.group(1):
            # 同じ日付なら現在のファイル自身を返す
            return current_file
    
    # 日付パターンを抽出（20260101形式）
    date_match = re.search(r'(\d{8})', decoded)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    
    # 同じ日付を持つファイルを検索
    for actual_file in actual_files.values():
        if date_str in actual_file:
            return actual_file
    
    return None

def fix_urls_in_file(filepath, actual_files):
    """1つのHTMLファイル内の不適切なURLを修正"""
    current_filename = Path(filepath).name
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # パターン1: href="xxxxx.html" (相対パス)
    def replace_href(match):
        full_match = match.group(0)
        url = match.group(1)
        
        # ASCII文字のみの場合はスキップ
        if url.isascii() and not any(char in url for char in ['%', '・', '（', '）']):
            return full_match
        
        filename = url.split('/')[-1]
        correct = find_correct_filename(filename, actual_files, current_filename)
        
        if correct and correct != filename:
            changes.append(f"  {filename} → {correct}")
            return f'href="{correct}"'
        return full_match
    
    content = re.sub(r'href="([^"]+\.html)"', replace_href, content)
    
    # パターン2: content="https://yui-love.vercel.app/posts/xxxxx.html" (絶対パス)
    def replace_content_url(match):
        full_match = match.group(0)
        url = match.group(1)
        
        filename = extract_filename_from_url(url)
        if not filename:
            return full_match
        
        # ASCII文字のみの場合はスキップ
        if filename.isascii() and not any(char in filename for char in ['%', '・', '（', '）']):
            return full_match
        
        correct = find_correct_filename(filename, actual_files, current_filename)
        
        if correct and correct != filename:
            new_url = BASE_URL + correct
            changes.append(f"  {url} → {new_url}")
            return f'content="{new_url}"'
        return full_match
    
    content = re.sub(r'content="(https://yui-love\.vercel\.app/posts/[^"]+\.html)"', replace_content_url, content)
    
    # パターン3: @id in JSON-LD
    def replace_jsonld_id(match):
        full_match = match.group(0)
        url = match.group(1)
        
        filename = extract_filename_from_url(url)
        if not filename:
            return full_match
        
        # ASCII文字のみの場合はスキップ
        if filename.isascii() and not any(char in filename for char in ['%', '・', '（', '）']):
            return full_match
        
        correct = find_correct_filename(filename, actual_files, current_filename)
        
        if correct and correct != filename:
            new_url = BASE_URL + correct
            changes.append(f"  {url} → {new_url}")
            return f'"@id": "{new_url}"'
        return full_match
    
    content = re.sub(r'"@id":\s*"(https://yui-love\.vercel\.app/posts/[^"]+\.html)"', replace_jsonld_id, content)
    
    # パターン4: rel="canonical" href="xxxxx.html" (相対パス)
    def replace_canonical(match):
        full_match = match.group(0)
        url = match.group(1)
        
        # ASCII文字のみの場合はスキップ
        if url.isascii() and not any(char in url for char in ['%', '・', '（', '）']):
            return full_match
        
        filename = url.split('/')[-1]
        correct = find_correct_filename(filename, actual_files, current_filename)
        
        if correct and correct != filename:
            changes.append(f"  canonical: {filename} → {correct}")
            return f'<link rel="canonical" href="{BASE_URL}{correct}">'
        return full_match
    
    content = re.sub(r'<link rel="canonical" href="([^"]+\.html)">', replace_canonical, content)
    
    # 変更があった場合のみファイルを更新
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    
    return []

def main():
    print("🔍 不適切なURLの検出と修正を開始します（改善版）...")
    print()
    
    # 実際のファイル名マップを作成
    actual_files = get_actual_filename_map()
    print(f"✅ {len(actual_files)} 個のHTMLファイルを検出しました")
    print()
    
    # postsディレクトリ内の全HTMLファイルを処理
    posts_path = Path(POSTS_DIR)
    total_files = 0
    fixed_files = 0
    total_changes = 0
    
    for html_file in sorted(posts_path.glob("*.html")):
        total_files += 1
        changes = fix_urls_in_file(html_file, actual_files)
        
        if changes:
            fixed_files += 1
            total_changes += len(changes)
            print(f"📝 {html_file.name}")
            for change in changes:
                print(change)
            print()
    
    print("=" * 60)
    print(f"✅ 処理完了")
    print(f"   対象ファイル: {total_files} 件")
    print(f"   修正ファイル: {fixed_files} 件")
    print(f"   修正箇所: {total_changes} 箇所")
    print("=" * 60)

if __name__ == "__main__":
    main()
