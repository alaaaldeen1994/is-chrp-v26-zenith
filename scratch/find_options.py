import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')
cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
with open(os.path.join(cwd, 'bridge_server.py'), 'r', encoding='utf-8', errors='ignore') as f:
    server = f.read()

# Find HybridDiscoveryRequest handler and cell_type options
# Extract cell_type handling logic
cell_idx = server.find('cell_type')
snippets = []
for m in re.finditer(r'cell_type[^"\']*["\']([^"\']{3,})["\']', server):
    snippets.append(m.group(1))
print('=== CELL TYPE OPTIONS DETECTED IN CODE ===')
print(set(snippets[:30]))

# Find repro_mode options
repro_modes = []
for m in re.finditer(r'repro_mode[^"\']*["\']([^"\']{2,})["\']', server):
    repro_modes.append(m.group(1))
print('\n=== REPRO MODE OPTIONS ===')
print(set(repro_modes[:20]))

# Find target_type options
target_types = []
for m in re.finditer(r'target_type[^"\']*["\']([^"\']{2,})["\']', server):
    target_types.append(m.group(1))
print('\n=== TARGET TYPE OPTIONS ===')
print(set(target_types[:20]))

# Find what /discover_hybrid endpoint signature looks like
disc_hyb = server.find('discover_hybrid')
if disc_hyb > 0:
    snippet = server[disc_hyb:disc_hyb+800]
    print('\n=== /discover_hybrid handler snippet ===')
    print(snippet[:600])
