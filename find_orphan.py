lines = open('index.html', encoding='utf-8', errors='replace').readlines()
# Find the orphaned block
for i, l in enumerate(lines, 1):
    if i >= 5298 and i <= 5445:
        print(i, l.rstrip()[:80])
