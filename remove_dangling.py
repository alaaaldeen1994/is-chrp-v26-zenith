import sys
sys.stdout.reconfigure(encoding='utf-8')
lines = open('index.html', encoding='utf-8', errors='replace').readlines()
print('Lines:', len(lines))

# Find the dangling old code — starts at line 5323 (0-indexed: 5322) 
# and ends at the next </script> tag
# Line 5320 = '}' (close of runDiscovery) — KEEP
# Line 5321 = '' — KEEP
# Lines 5322+ = old code — REMOVE until </script>

end_idx = None
for i in range(5321, len(lines)):
    if '</script>' in lines[i]:
        end_idx = i
        print(f'Found </script> at line {i+1}')
        break

if end_idx:
    # Remove lines 5322 to end_idx-1 (keep </script>)
    clean = lines[:5321] + lines[end_idx:]
    print(f'Removed {end_idx - 5321} lines of old code')
    print('Line 5321:', repr(lines[5320].rstrip()))
    print('Line 5322 after:', repr(clean[5321].rstrip()[:50]))
    open('index.html', 'w', encoding='utf-8').write(''.join(clean))
    print('DONE')
else:
    print('No </script> found')
