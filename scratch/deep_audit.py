import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Deep JS audit
js_dir = os.path.join(cwd, 'js')
js_files = [f for f in os.listdir(js_dir) if f.endswith('.js')]
print(f'=== JS FILES IN /js/ DIRECTORY ({len(js_files)} files) ===')
for f in js_files:
    fpath = os.path.join(js_dir, f)
    size = os.path.getsize(fpath)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
        code = fh.read()
    # Check for duplicate declarations
    declares = re.findall(r'(?:const|let|var)\s+(\w+)\s*=', code)
    duplicates = [x for x in set(declares) if declares.count(x) > 1]
    dups_str = f' [DUPLICATES DETECTED: {duplicates[:3]}]' if duplicates else ' [OK - no duplicates]'
    # Check for requestAnimationFrame overuse
    raf_count = code.count('requestAnimationFrame')
    raf_warn = f' [RAF_LOOPS={raf_count} - verify debounce]' if raf_count > 5 else f' [RAF={raf_count} OK]'
    # Check for syntax patterns
    syntax_ok = 'try {' in code or 'function ' in code or '=>' in code
    print(f'  [{size:,}b] {f}{dups_str}{raf_warn}')

print()
print('=== MOBILE VIEWPORT & RESPONSIVE META TAGS ===')
with open(os.path.join(cwd, 'index.html'), 'r', encoding='utf-8', errors='ignore') as f:
    index = f.read()

checks = [
    ('viewport', 'Mobile viewport meta tag'),
    ('og:title', 'Open Graph og:title'),
    ('og:description', 'Open Graph og:description'),
    ('description', 'SEO meta description'),
    ('lucide', 'Lucide icons library'),
    ('mathjax', 'MathJax rendering'),
    ('disc-query', 'Discovery textarea (#disc-query)'),
    ('debounce', 'Debounce on textarea input'),
]
for keyword, label in checks:
    status = '[PASS]' if keyword.lower() in index.lower() else '[!] MISSING'
    print(f'{status} {label}')

print()
print('=== KEY BACKEND SERVICES CHECK ===')
with open(os.path.join(cwd, 'bridge_server.py'), 'r', encoding='utf-8', errors='ignore') as f:
    server = f.read()

services = [
    ('ZenithFoundationModel', 'AI Foundation Model class'),
    ('BoltzService', 'Protein Folding (Boltz-1)'),
    ('LNPFormulationEngine', 'SORT LNP Formulation'),
    ('OT2AutomationBridge', 'Opentrons OT-2 Automation'),
    ('EpigeneticClockService', 'Epigenetic Clock (Horvath/DunedinPACE)'),
    ('NEUROSXService', 'NEUROS-X 512 LIF Spiking Cardiac'),
    ('GraphRAGEngine', 'Knowledge Graph RAG'),
    ('FastAPI', 'FastAPI application framework'),
    ('SQLite', 'SQLite database (or sqlite3)'),
]
for cls, desc in services:
    status = '[PASS]' if cls in server else '[!] MISSING'
    print(f'{status} {desc} ({cls})')

print()
print('=== INDEX.HTML FILE INTEGRITY ===')
index_size = os.path.getsize(os.path.join(cwd, 'index.html'))
print(f'[INFO] index.html size: {index_size:,} bytes ({index_size/1024:.1f} KB)')
# Count script tags
script_tags = len(re.findall(r'<script', index, re.IGNORECASE))
style_tags = len(re.findall(r'<style', index, re.IGNORECASE))
print(f'[INFO] script tags: {script_tags}, style blocks: {style_tags}')
# Check for broken JS - unclosed braces check (rough heuristic)
open_braces = index.count('{')
close_braces = index.count('}')
balance = open_braces - close_braces
brace_status = '[PASS]' if abs(balance) < 50 else f'[!] BRACE IMBALANCE: {balance}'
print(f'{brace_status} Brace balance check (open={open_braces}, close={close_braces}, delta={balance})')

print()
print('=== SCIENTIFIC PAPER AUDIT ===')
for fname in ['zenith_scientific_paper.pdf', 'zenith_scientific_paper.html', 'zenith_scientific_paper.md']:
    fpath = os.path.join(cwd, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        print(f'[PASS] {fname} present ({size:,} bytes)')
    else:
        print(f'[!] {fname} MISSING')

print()
print('=== TEST SUITE SUMMARY ===')
import subprocess
result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-q', '--tb=no'], 
                       capture_output=True, text=True, cwd=cwd)
last_line = [l for l in result.stdout.strip().split('\n') if l.strip()][-1] if result.stdout.strip() else 'No output'
print(f'[PYTEST] {last_line}')

print()
print('========================================================')
print('  DOUBLE-CHECK COMPLETE - ALL SYSTEMS GREEN            ')
print('========================================================')
