import os, re, shutil

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Copy tight-cropped logo to assets folder too
src = os.path.join(base, 'Bhaa_tight.png')
dst_assets = os.path.join(base, 'assets', 'Bhaa_tight.png')
shutil.copy2(src, dst_assets)
print('Copied to assets/')

# Now update all HTML files - replace hosted URL img with local tight-cropped file
old_pattern = r'<a href="index\.html"[^>]*><img src="https://www\.image2url\.com[^"]*"[^>]*></a>'

new_logo = '<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="Bhaa_tight.png" alt="Nilus Lab" style="height:40px;width:auto;display:block;transition:opacity 0.2s;" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

files = ['api.html', 'index.html', 'index_9a4de71.html', 'index_backup_9688caa.html', 'index_c4a3865.html', 'profile.html']

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

print('DONE!')
