lines = open('index.html', encoding='utf-8', errors='replace').readlines()
print('Before:', len(lines), 'lines')
# Remove lines 5301-5414 (0-indexed: 5300-5413)
# Line 5300 (0-indexed) = '}' (closing of runDiscovery) - KEEP
# Lines 5301-5413 = orphan block - REMOVE
# Line 5414 (0-indexed) = '}' - but this is a duplicate close, remove too
# Line 5415 = '</script>' - KEEP

clean = lines[:5300] + lines[5415:]  # 0-indexed
print('After:', len(clean), 'lines')
# verify
print('Line ~5300:', repr(clean[5299].rstrip()[:40]))
print('Line ~5301:', repr(clean[5300].rstrip()[:40]))
open('index.html', 'w', encoding='utf-8').write(''.join(clean))
print('Done!')
