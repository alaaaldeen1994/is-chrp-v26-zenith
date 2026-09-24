import glob
import re

for path in glob.glob('*.html'):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = re.findall(r'href=["\']([^"\']*\.pdf)["\']', content, re.I)
            if matches:
                print(f"{path}: {matches}")
    except Exception as e:
        pass
