import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

with open(os.path.join(cwd, 'index.html'), 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Find biomarker-related UI elements
patterns = [
    'disc-query', 'biomarker', 'cell-type', 'cell_type', 'repro-mode',
    'reprogramming-mode', 'stability', 'age-delta', 'submit', 'run-discovery',
    'discover', 'real-discovery', 'gpt-discovery'
]

print('=== BIOMARKER UI ELEMENTS IN INDEX.HTML ===')
for p in patterns:
    occurrences = [m.start() for m in re.finditer(p, html, re.IGNORECASE)]
    if occurrences:
        # Grab surrounding context for first occurrence
        idx = occurrences[0]
        snippet = html[max(0,idx-60):idx+120].replace('\n','').replace('  ','')
        print(f'\n[{p}] ({len(occurrences)} hits)')
        print(f'  Context: ...{snippet}...')

# Find cell type <select> or <option> tags
print('\n\n=== CELL TYPE DROPDOWN OPTIONS ===')
select_matches = re.findall(r'<option[^>]*value=["\']([^"\']*)["\'][^>]*>([^<]*)<', html, re.IGNORECASE)
cell_opts = [(v,t) for v,t in select_matches if any(k in t.lower() or k in v.lower() for k in ['cardiac','fibro','myocyte','cell','cardiomy','heart','all'])]
for val, text in cell_opts[:20]:
    print(f'  value="{val}" -> {text.strip()}')

# Find reprogramming mode options
print('\n=== REPROGRAMMING MODE OPTIONS ===')
repro_opts = [(v,t) for v,t in select_matches if any(k in t.lower() or k in v.lower() for k in ['zenith','gpt','partial','complete','full','reprog','mode'])]
for val, text in repro_opts[:20]:
    print(f'  value="{val}" -> {text.strip()}')
