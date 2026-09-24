import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
logo_url = 'https://www.image2url.com/r2/default/images/1785736147288-9b578841-9a38-49bb-ba20-023295c5d884.jpg'

# Old small logo style
old_pattern = r'<img src="https://www\.image2url\.com/r2/default/images/1785736147288-9b578841-9a38-49bb-ba20-023295c5d884\.jpg"[^>]*>'

# New larger, professional logo
new_logo = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;"><img src="{logo_url}" alt="Nilus Lab" style="height:52px;width:auto;object-fit:contain;display:block;filter:drop-shadow(0 1px 4px rgba(0,0,0,0.08));transition:opacity 0.2s;" onmouseover="this.style.opacity=0.85" onmouseout="this.style.opacity=1"></a>'

files = [
    'api.html', 'index.html', 'index_9a4de71.html',
    'index_backup_9688caa.html', 'index_c4a3865.html', 'profile.html'
]

for fn in files:
    fp = os.path.join(base, fn)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content
    content = re.sub(old_pattern, new_logo, content, flags=re.DOTALL)
    if content != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {fn}')
    else:
        print(f'NO CHANGE: {fn}')

print('ALL DONE!')
