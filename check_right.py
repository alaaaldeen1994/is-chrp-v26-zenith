content = open('index.html', encoding='utf-8', errors='replace').read()

# Check what's around the right panel header
idx = content.find('RIGHT: AI PROTOCOL DISCOVERY PANEL')
if idx < 0:
    print('Right panel comment not found')
else:
    print('Found at char', idx)
    print(repr(content[idx-200:idx+100]))
