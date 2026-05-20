import sys
sys.stdout.reconfigure(encoding='utf-8')
lines = open('index.html', encoding='utf-8', errors='replace').readlines()
print('Total lines:', len(lines))

# Find the old two-column layout block
start_idx = None
end_idx = None
for i in range(1103, len(lines)):
    l = lines[i]
    if '<!-- TWO-COLUMN MAIN AREA -->' in l and start_idx is None:
        # Go back 2 lines to include the Title row div
        start_idx = i - 2  # include the title row
        print(f'Old block start at line {start_idx+1}')
    if start_idx and '<!-- ═══ VIEW 2' in l:
        end_idx = i
        print(f'Old block end at line {i+1}')
        break

if start_idx and end_idx:
    clean = lines[:start_idx] + lines[end_idx:]
    print(f'Removing {end_idx - start_idx} lines')
    open('index.html', 'w', encoding='utf-8').write(''.join(clean))
    print('Done! New total:', len(clean))
else:
    print(f'start={start_idx}, end={end_idx}')
    # Show around line 1103
    for i in range(1100, 1118):
        print(i+1, lines[i].rstrip()[:70])
