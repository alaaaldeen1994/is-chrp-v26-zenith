import sys
sys.stdout.reconfigure(encoding='utf-8')
lines = open('index.html', encoding='utf-8', errors='replace').readlines()
print('Total lines:', len(lines))

# Find the end of runDiscovery (line 5300 = closing })
# Find the first non-empty content AFTER line 5300 in the script tag context
for i in range(5299, min(5444, len(lines))):
    l = lines[i].rstrip()
    if l.strip():
        print(i+1, repr(l[:60]))
    if '</script>' in l or 'system-footer' in l:
        print(f'FOUND END at line {i+1}')
        break
