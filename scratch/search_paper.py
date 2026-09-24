import glob, os

query = "zenith_scientific_paper"

for root, dirs, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith(('.html', '.js', '.py', '.md', '.txt', '.json')):
            p = os.path.join(root, file)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if query in line:
                            print(f"{p}:{idx}: {line.strip()}")
            except Exception:
                pass
