lines = open('index.html', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines, 1):
    if 'toast-feed' in l or 'architect-layout' in l or 'mobile-shell' in l:
        print(i, l.rstrip()[:100])
