import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Rule to append to CSS files and HTML style blocks to force horizontal navbar layout on mobile
nav_fix_css = """
/* Guarantee Horizontal Navbar Layout on Mobile & Desktop */
nav, .nav-dock, #mob-nav {
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
}

@media (max-width: 1024px) {
    nav, .nav-dock {
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        padding: 0.75rem 1.25rem !important;
    }
}
"""

# Update CSS files
css_files = ['nilus_institutional.css', 'profile_minimal.css', 'style.css']
for cfn in css_files:
    cfp = os.path.join(base, 'css', cfn)
    if os.path.exists(cfp):
        with open(cfp, 'r', encoding='utf-8', errors='ignore') as f:
            ccontent = f.read()
        if 'Guarantee Horizontal Navbar Layout' not in ccontent:
            ccontent += "\n" + nav_fix_css
            with open(cfp, 'w', encoding='utf-8') as f:
                f.write(ccontent)
            print(f"Updated CSS: {cfn}")

# Update HTML files - fix flex-direction: column under @media for nav
html_files = glob.glob(os.path.join(base, '*.html'))

updated_html = []
for hpath in html_files:
    hfn = os.path.basename(hpath)
    with open(hpath, 'r', encoding='utf-8', errors='ignore') as f:
        hcontent = f.read()
    
    orig = hcontent
    
    # 1. Replace nav { ... flex-direction: column; ... }
    hcontent = re.sub(
        r'(nav\s*\{[^}]*?)flex-direction\s*:\s*column;?',
        r'\1flex-direction: row !important;',
        hcontent,
        flags=re.IGNORECASE
    )
    
    # 2. Inject nav_fix_css before </head> if not already present
    if 'Guarantee Horizontal Navbar Layout' not in hcontent and '</head>' in hcontent:
        hcontent = hcontent.replace('</head>', f'<style>{nav_fix_css}</style>\n</head>')

    if hcontent != orig:
        with open(hpath, 'w', encoding='utf-8') as f:
            f.write(hcontent)
        updated_html.append(hfn)

print(f"Updated {len(updated_html)} HTML files:")
for f in updated_html:
    print(" -", f)
