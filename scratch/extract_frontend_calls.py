import glob
import re

endpoints = set()
for filepath in glob.glob('*.html') + glob.glob('js/*.js'):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Find fetch calls
        for match in re.finditer(r'fetch\s*\(\s*[\'"`]([^\'"`\?\#\s]+)', content):
            url = match.group(1)
            endpoints.add((filepath, url))
    except Exception as e:
        pass

print("Extracted frontend endpoints:")
for fp, url in sorted(endpoints):
    if url.startswith('/') or 'localhost' in url or 'nilus' in url:
        print(f"{fp:30} -> {url}")
