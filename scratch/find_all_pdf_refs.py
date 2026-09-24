import os, glob, re

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.py', '.md')):
            p = os.path.join(root, file)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    matches = re.findall(r'[^"\']*\.pdf', content)
                    if matches:
                        print(f"{p}: {matches}")
            except Exception:
                pass
