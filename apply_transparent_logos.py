import os, glob, re, base64, shutil

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Save copies into assets/
shutil.copy2(os.path.join(base, 'Bhaa_transparent.png'), os.path.join(base, 'assets', 'Bhaa_transparent.png'))
shutil.copy2(os.path.join(base, 'Bhaa_transparent_darkmode.png'), os.path.join(base, 'assets', 'Bhaa_transparent_darkmode.png'))
print("Saved transparent logos to assets/")

# Load Base64 strings
with open(os.path.join(base, 'Bhaa_transparent.png'), 'rb') as f:
    b64_light = base64.b64encode(f.read()).decode('utf-8')

with open(os.path.join(base, 'Bhaa_transparent_darkmode.png'), 'rb') as f:
    b64_dark = base64.b64encode(f.read()).decode('utf-8')

logo_light_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_light}" alt="Nilus Lab" class="nav-logo-responsive" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

logo_dark_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_dark}" alt="Nilus Lab" class="nav-logo-responsive" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

html_files = glob.glob(os.path.join(base, '*.html'))

updated = []

for hpath in sorted(html_files):
    hfn = os.path.basename(hpath)
    with open(hpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    orig = content
    
    # In mob-nav-brand or dark header elements, use logo_dark_tag
    if 'mob-nav-brand' in content:
        content = re.sub(
            r'<div class="mob-nav-brand">\s*<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>\s*</div>',
            f'<div class="mob-nav-brand">{logo_dark_tag}</div>',
            content
        )
    
    # In all other navbar containers (like .nav-dock), replace any old base64 logo with logo_light_tag
    content = re.sub(
        r'<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>',
        logo_light_tag,
        content
    )

    if content != orig:
        with open(hpath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated.append(hfn)

print(f"Updated {len(updated)} HTML files with transparent base64 logos:")
for f in updated:
    print(" -", f)
