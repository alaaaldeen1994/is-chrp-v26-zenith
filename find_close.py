lines = open('index.html', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines, 1):
    if '</body>' in l or '</html>' in l:
        print(i, repr(l[:60]))
