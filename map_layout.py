lines = open('index.html', encoding='utf-8', errors='replace').readlines()
keywords = ['architect-layout', 'id="nav', 'id="top', 'biosim-canvas', 'left-panel', 'right-panel', 'center-panel', 'id="canvas', '<body', 'ai-panel', 'id="sim', 'protocol-scroll']
for i, l in enumerate(lines, 1):
    for kw in keywords:
        if kw in l:
            print(i, l.rstrip()[:110])
            break
