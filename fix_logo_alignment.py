import os, glob, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Load Base64 strings for transparent light and dark logos
with open(os.path.join(base, 'Bhaa_transparent.png'), 'rb') as f:
    b64_light = base64.b64encode(f.read()).decode('utf-8')

with open(os.path.join(base, 'Bhaa_transparent_darkmode.png'), 'rb') as f:
    b64_dark = base64.b64encode(f.read()).decode('utf-8')

# Perfect size and vertical alignment CSS for nav logo
# 38px height + -4px translateY nudges NILUS LAB text into perfect horizontal alignment with navbar links
logo_css = """
/* Executive Navbar Logo Alignment & Responsive Sizing */
.nav-logo-responsive {
    height: 38px !important;
    width: auto !important;
    max-height: 38px !important;
    object-fit: contain;
    display: block;
    transform: translateY(-3px);
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.nav-logo-responsive:hover {
    opacity: 0.85;
}

@media (max-width: 768px) {
    .nav-logo-responsive {
        height: 32px !important;
        max-height: 32px !important;
        transform: translateY(-2px);
    }
}
"""

logo_light_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_light}" alt="Nilus Lab" class="nav-logo-responsive"></a>'

logo_dark_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_dark}" alt="Nilus Lab" class="nav-logo-responsive"></a>'

# Update CSS files
css_files = ['nilus_institutional.css', 'profile_minimal.css', 'style.css']
for cfn in css_files:
    cfp = os.path.join(base, 'css', cfn)
    if os.path.exists(cfp):
        with open(cfp, 'r', encoding='utf-8', errors='ignore') as f:
            ccontent = f.read()
        # Replace or update Executive Navbar Logo Alignment
        if 'Executive Navbar Logo Alignment' in ccontent:
            ccontent = re.sub(r'/\* Executive Navbar Logo Alignment [\s\S]*?\n\}', logo_css.strip(), ccontent)
        else:
            ccontent += "\n" + logo_css
        with open(cfp, 'w', encoding='utf-8') as f:
            f.write(ccontent)
        print(f"Updated CSS: {cfn}")

# Update HTML files
html_files = glob.glob(os.path.join(base, '*.html'))

updated = []

for hpath in sorted(html_files):
    hfn = os.path.basename(hpath)
    with open(hpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    orig = content
    
    # 1. Update logo tag height in inline styles / base64 tags
    content = re.sub(
        r'<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>',
        logo_light_tag,
        content
    )
    
    # 2. For mob-nav-brand, use dark logo tag
    if 'mob-nav-brand' in content:
        content = re.sub(
            r'<div class="mob-nav-brand">\s*<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>\s*</div>',
            f'<div class="mob-nav-brand">{logo_dark_tag}</div>',
            content
        )
    
    # 3. Ensure logo_css is injected in <style> block if present
    if 'Executive Navbar Logo Alignment' not in content and '</head>' in content:
        content = content.replace('</head>', f'<style>{logo_css}</style>\n</head>')
    elif 'Executive Navbar Logo Alignment' in content:
        content = re.sub(r'/\* Executive Navbar Logo Alignment [\s\S]*?\n\}', logo_css.strip(), content)

    if content != orig:
        with open(hpath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated.append(hfn)

print(f"Updated {len(updated)} HTML files with 38px nudged logo:")
for f in updated:
    print(" -", f)
