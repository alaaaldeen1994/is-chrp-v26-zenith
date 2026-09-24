import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

with open(os.path.join(base, 'Bhaa_tight.png'), 'rb') as f:
    import base64
    b64 = base64.b64encode(f.read()).decode('utf-8')

logo_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64}" alt="Nilus Lab" style="height:52px;width:auto;display:block;transition:opacity 0.2s;" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

print("Logo tag generated, length:", len(logo_tag))

html_files = glob.glob(os.path.join(base, '*.html'))

updated = []
skipped = []

for filepath in sorted(html_files):
    fname = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    orig = content
    
    # 1. Replace existing base64 img logo tag (with 40px or whatever height)
    content = re.sub(
        r'<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>',
        logo_tag,
        content
    )
    
    # 2. Replace lucide layers icon + NILUS LAB text blocks
    content = re.sub(
        r'<div class="flex items-center gap-2">\s*<i data-lucide="layers"[^>]*></i>\s*<div class="font-sans font-bold tracking-tighter flex items-center uppercase text-slate-900 leading-none">\s*<span class="text-xl mr-1">NILUS <span class="text-blue-600 ml-1">LAB</span></span>\s*</div>\s*</div>',
        logo_tag,
        content
    )
    
    # 3. Replace standalone SVG layers logo + NILUS LAB text blocks (like in mob-nav-brand or nav-brand)
    content = re.sub(
        r'<svg[^>]*>[\s\S]{0,500}?</svg>\s*\n?\s*NILUS\s*<span[^>]*>LAB</span>',
        logo_tag,
        content
    )
    
    # 4. Replace <img src="Bhaa.jpg"...> or <img src="Bhaa_tight.png"...> or hosted URLs
    content = re.sub(
        r'<a href="index\.html"[^>]*><img src="(?:Bhaa[^"]*|https://www\.image2url\.com[^"]*)"[^>]*></a>',
        logo_tag,
        content
    )
    content = re.sub(
        r'<img src="(?:Bhaa[^"]*|https://www\.image2url\.com[^"]*)"[^>]*>',
        logo_tag,
        content
    )

    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        updated.append(fname)
    else:
        skipped.append(fname)

print("\nUpdated files (", len(updated), "):")
for f in updated:
    print("  -", f)

print("\nSkipped files (", len(skipped), "):")
for f in skipped:
    print("  -", f)
