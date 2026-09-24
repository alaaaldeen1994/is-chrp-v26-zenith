with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('runDiscovery')
if idx != -1:
    print(html[idx-100:idx+2500])
