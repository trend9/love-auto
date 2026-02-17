import os

GA_TAG = """    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-NGYD7E9JVG"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag() { dataLayer.push(arguments); }
        gtag('js', new Date());

        gtag('config', 'G-NGYD7E9JVG');
    </script>
"""

DIRS_TO_PROCESS = ["posts"]

def add_analytics():
    count = 0
    for d in DIRS_TO_PROCESS:
        if not os.path.exists(d):
            continue
        for filename in os.listdir(d):
            if filename.endswith(".html"):
                path = os.path.join(d, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if "G-NGYD7E9JVG" in content:
                    continue
                
                # Insert after <head>
                if "<head>" in content:
                    new_content = content.replace("<head>", f"<head>\n{GA_TAG}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Added GA4 to: {path}")
                    count += 1
                else:
                    print(f"Warning: No <head> tag found in {path}")
                    
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    add_analytics()
