import os, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Read the tight-cropped logo and encode as base64
img_path = os.path.join(base, 'Bhaa_tight.png')
with open(img_path, 'rb') as f:
    img_data = f.read()

b64 = base64.b64encode(img_data).decode('utf-8')
data_uri = f'data:image/png;base64,{b64}'
print(f'Base64 length: {len(b64)} chars')

# Build the new logo tag with embedded base64
new_logo = (
    '<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;">'
    '<img src="' + data_uri + '" '
    'alt="Nilus Lab" '
    'style="height:40px;width:auto;display:block;transition:opacity 0.2s;" '
    'onmouseover="this.style.opacity=.8" '
    'onmouseout="this.style.opacity=1">'
    '</a>'
)

# Pattern to match the current broken local path logo
old_pattern = r'<a href="index\.html"[^>]*><img src="Bhaa_tight\.png"[^>]*></a>'

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
