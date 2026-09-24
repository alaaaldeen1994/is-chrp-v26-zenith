import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('const loadLabel = mode === \'real\'')
if idx != -1:
    print(html[idx+1200:idx+4500])
