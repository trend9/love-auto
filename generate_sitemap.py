import json
import os
from datetime import datetime

BASE_URL = "https://yui-love.vercel.app/"
JSON_FILE = "data/questions.json"
SITEMAP_ROOT = "sitemap.xml"
SITEMAP_PUBLIC = "public/sitemap.xml"

def generate_sitemap():
    if not os.path.exists(JSON_FILE):
        print(f"Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    # Static pages
    urls = [
        {"loc": f"{BASE_URL}index.html", "lastmod": datetime.now().strftime("%Y-%m-%d"), "priority": "1.0"},
        {"loc": f"{BASE_URL}archive.html", "lastmod": datetime.now().strftime("%Y-%m-%d"), "priority": "0.8"},
        {"loc": f"{BASE_URL}profile.html", "lastmod": datetime.now().strftime("%Y-%m-%d"), "priority": "0.5"},
    ]

    # Posts
    for post in posts:
        # date format in json is YYYY.MM.DD
        lastmod = post["date"].replace(".", "-")
        urls.append({
            "loc": f"{BASE_URL}{post['url']}",
            "lastmod": lastmod,
            "priority": "0.6"
        })

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url["loc"]}</loc>\n'
        xml_content += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
        xml_content += f'    <priority>{url["priority"]}</priority>\n'
        xml_content += '  <url>\n' # Note: sitemap.xml uses <url> ... </url>, let me fix the closing tag

    # Actually, fixing the closing tag
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml_content += '  <url>\n'
        xml_content += f'    <loc>{url["loc"]}</loc>\n'
        xml_content += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
        xml_content += f'    <priority>{url["priority"]}</priority>\n'
        xml_content += '  </url>\n'
    xml_content += '</urlset>'

    with open(SITEMAP_ROOT, "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    with open(SITEMAP_PUBLIC, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"Sitemap generated: {SITEMAP_ROOT} and {SITEMAP_PUBLIC}")

if __name__ == "__main__":
    generate_sitemap()
