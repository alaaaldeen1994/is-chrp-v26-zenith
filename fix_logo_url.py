import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
logo_url = 'https://www.image2url.com/r2/default/images/1785736147288-9b578841-9a38-49bb-ba20-023295c5d884.jpg'
new_logo = f'<img src="{logo_url}" alt="Nilus Lab Logo" style="height:38px;width:auto;object-fit:contain;display:block;">'

files = [
    'api.html', 'discovery_mockup.html', 'index.html',
    'index_9a4de71.html', 'index_backup_9688caa.html',
    'index_c4a3865.html', 'profile.html', 'technical_catalog.html',
    'about.html', 'contact.html', 'evidence.html', 'how_it_works.html',
    'legal.html', 'login.html', 'regulatory.html', 'scientific_qna.html',
    'structure.html', 'trials.html', 'whitepaper.html', 'v26_clinical_report.html',
    'v30_clinical_report.html', 'pilot_dashboard.html'
]

patterns = [
    # Pattern 1: Already replaced Bhaa.jpg - update to URL
    r'<img src="Bhaa\.jpg"[^>]*>',
    # Pattern 2: lucide layers icon + NILUS LAB flex div
    r'<div class="flex items-center gap-2">\s*\n?\s*<i data-lucide="layers"[^>]*></i>[\s\S]{0,300}?NILUS[\s\S]{0,100}?LAB[\s\S]{0,50}?</span>\s*\n?\s*</div>\s*\n?\s*</div>',
    # Pattern 3: SVG inline layers + NILUS LAB text in mob-nav
    r'<svg[^>]*>[\s\S]{0,500}?</svg>\s*\n?\s*NILUS\s*<span[^>]*>LAB</span>',
    # Pattern 4: standalone layers icon + NILUS text block
    r'<i data-lucide="layers"[^>]*></i>[\s\S]{0,200}?NILUS[\s\S]{0,100}?LAB</span>[\s\S]{0,50}?</div>',
]

for fn in files:
    fp = os.path.join(base, fn)
    if not os.path.exists(fp):
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
        print(f'NO CHANGE: {fn}')

print('ALL DONE!')
