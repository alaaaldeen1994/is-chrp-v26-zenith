import os, glob, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Load Bhaa_tight.png as base64
with open(os.path.join(base, 'Bhaa_tight.png'), 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

logo_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64}" alt="Nilus Lab" style="height:52px;width:auto;display:block;transition:opacity 0.2s;" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

html_files = glob.glob(os.path.join(base, '*.html'))

updated_files = []

for filepath in sorted(html_files):
    fname = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    orig = content
    
    # 1. Update any existing base64 img logo tag to have height:52px
    content = re.sub(
        r'(<img src="data:image/png;base64,[^"]+")[^>]*style="[^"]*"',
        r'\1 alt="Nilus Lab" style="height:52px;width:auto;display:block;transition:opacity 0.2s;" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"',
        content
    )
    
    # 2. Replace flex items-center gap-2 containing SVG/lucide + NILUS LAB text
    content = re.sub(
        r'<div class="flex items-center gap-2">\s*(?:<svg[^>]*>[\s\S]*?</svg>|<i data-lucide="[^"]*"[^>]*></i>)\s*<div[^>]*>\s*<span[^>]*>NILUS\s*<span[^>]*>LAB</span></span>\s*</div>\s*</div>',
        logo_tag,
        content,
        flags=re.IGNORECASE
    )
    
    # 3. Replace loose svg/lucide + NILUS LAB block in header/nav
    content = re.sub(
        r'(?:<svg[^>]*>[\s\S]*?</svg>|<i data-lucide="layers"[^>]*></i>)\s*<div[^>]*font-sans[^>]*>\s*<span[^>]*>NILUS\s*<span[^>]*>LAB</span></span>\s*</div>',
        logo_tag,
        content,
        flags=re.IGNORECASE
    )
    
    # 4. Replace mob-nav-brand with SVG + NILUS LAB
    content = re.sub(
        r'<div class="mob-nav-brand">\s*<svg[^>]*>[\s\S]*?</svg>\s*NILUS\s*<span[^>]*>LAB</span>\s*</div>',
        f'<div class="mob-nav-brand">{logo_tag}</div>',
        content,
        flags=re.IGNORECASE
    )

    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated_files.append(fname)

print(f"Successfully updated {len(updated_files)} files:")
for f in updated_files:
    print(" -", f)
