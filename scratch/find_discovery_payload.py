import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

with open(os.path.join(cwd, 'index.html'), 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Find the actual payload sent by the real-discovery fetch call
disc_idx = html.find('/api/real-discovery/run')
if disc_idx > 0:
    snippet = html[disc_idx-200:disc_idx+800]
    print('=== REAL DISCOVERY FETCH PAYLOAD ===')
    print(snippet)

print('\n\n=== GPT DISCOVERY FETCH PAYLOAD ===')
gpt_idx = html.find('/api/gpt-discovery/run')
if gpt_idx > 0:
    snippet = html[gpt_idx-200:gpt_idx+800]
    print(snippet)

# Find cell type selector in HTML
print('\n\n=== CELL TYPE SELECTOR ELEMENT ===')
ct_idx = html.find('cell-type-selector')
if ct_idx < 0:
    ct_idx = html.find('cellTypeSelector')
if ct_idx < 0:
    ct_idx = html.find('ct-selector')
if ct_idx < 0:
    # Try to find disc-query textarea surroundings to see its sibling controls
    dq_idx = html.find('id="disc-query"')
    if dq_idx > 0:
        print(html[dq_idx-500:dq_idx+1000])
