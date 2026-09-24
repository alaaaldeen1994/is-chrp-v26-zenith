with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('async function runDiscovery()')
if idx != -1:
    print(html[idx:idx+2500])
