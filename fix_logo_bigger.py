import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

files = ['api.html', 'index.html', 'index_9a4de71.html', 'index_backup_9688caa.html', 'index_c4a3865.html', 'profile.html']

for fn in files:
    fp = os.path.join(base, fn)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    original = content
    # Just change the height value on the base64 logo img tag
    content = content.replace(
        'src="data:image/png;base64,' , 'src="data:image/png;base64,'  # no-op to confirm pattern
    )
    # Change height:40px to height:52px only on the logo img
    content = re.sub(
        r'(<img src="data:image/png;base64,[^"]+")[^>]*style="height:40px;width:auto',
        r'\1 alt="Nilus Lab" style="height:52px;width:auto',
        content
    )
    if content != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'UPDATED: {fn}')
    else:
        print(f'NO CHANGE: {fn}')

print('DONE!')
