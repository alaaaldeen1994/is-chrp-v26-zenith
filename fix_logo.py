import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
new_logo = '<img src="Bhaa.jpg" alt="Nilus Lab Logo" style="height:38px;width:auto;object-fit:contain;display:block;">'

files = [
    'api.html', 'discovery_mockup.html', 'index.html',
    'index_9a4de71.html', 'index_backup_9688caa.html',
    'index_c4a3865.html', 'profile.html', 'technical_catalog.html'
]

patterns = [
    # Pattern 1: lucide layers icon + NILUS LAB div (profile.html style)
    r'<i data-lucide="layers"[^>]*></i>[\s\S]{0,200}?<span[^>]*>NILUS\s*<span[^>]*>LAB</span></span>[\s\S]{0,50}?</div>',
    # Pattern 2: SVG inline layers + NILUS LAB text (mob-nav-brand style)
    r'<svg[^>]*>[\s\S]{0,500}?</svg>\s*\n?\s*NILUS\s*<span[^>]*>LAB</span>',
    # Pattern 3: flex gap-2 div with layers icon
    r'<div class="flex items-center gap-2">\s*\n?\s*<i data-lucide="layers"[^>]*></i>[\s\S]{0,200}?</div>\s*\n?\s*</div>',
]

for fn in files:
    fp = os.path.join(base, fn)
    if not os.path.exists(fp):
        print(f'NOT FOUND: {fn}')
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content
    for pat in patterns:
        content = re.sub(pat, new_logo, content, flags=re.DOTALL)
    if content != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {fn}')
    else:
        print(f'NO MATCH: {fn}')

print('ALL DONE!')
