import os
import re

OLD_DOMAIN = "https://trend9.github.io/love-auto/"
NEW_DOMAIN = "https://yui-love.vercel.app/"
OLD_CLASS = "アドバイス-list"
NEW_CLASS = "advice-list"

FILES_TO_CHECK = [".html"]
DIRS_TO_CHECK = [".", "posts"]

def repair_urls():
    count = 0
    for d in DIRS_TO_CHECK:
        if not os.path.exists(d): continue
        for filename in os.listdir(d):
            if any(filename.endswith(ext) for ext in FILES_TO_CHECK):
                path = os.path.join(d, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if OLD_DOMAIN in content or OLD_CLASS in content:
                    new_content = content.replace(OLD_DOMAIN, NEW_DOMAIN).replace(OLD_CLASS, NEW_CLASS)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Repaired: {path}")
                    count += 1
    print(f"Total files repaired: {count}")

if __name__ == "__main__":
    repair_urls()
