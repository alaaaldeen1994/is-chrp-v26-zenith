import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('async function runDiscovery()')
if idx != -1:
    print(html[idx+5000:idx+8500])
