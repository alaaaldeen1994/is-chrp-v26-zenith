import re
with open('structure.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
for m in re.finditer(r'<button[^>]*>', text):
    tag = m.group(0)
    if 'predict' in tag.lower() or 'data-style' in tag.lower() or 'run' in tag.lower():
        print(tag)
