import os, glob, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Load Bhaa_tight.png as base64
with open(os.path.join(base, 'Bhaa_tight.png'), 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

logo_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64}" alt="Nilus Lab" class="nav-logo-responsive" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

# CSS block for responsive logo
logo_css = """
/* Responsive Navigation Logo Styling */
.nav-logo-responsive {
    height: 52px;
    width: auto;
    max-height: 52px;
    object-fit: contain;
    display: block;
    transition: opacity 0.2s ease;
}
@media (max-width: 768px) {
    .nav-logo-responsive {
        height: 34px !important;
        max-height: 34px !important;
    }
    .mob-nav-brand img, #mob-nav img {
        height: 32px !important;
        max-height: 32px !important;
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
        if 'nav-logo-responsive' not in ccontent:
            ccontent += "\n" + logo_css
            with open(cfp, 'w', encoding='utf-8') as f:
                f.write(ccontent)
            print(f"Updated CSS: {cfn}")

# Update HTML files to use class="nav-logo-responsive"
html_files = ['api.html', 'evidence.html', 'index.html', 'index_9a4de71.html', 'index_backup_9688caa.html', 'index_c4a3865.html', 'profile.html', 'scientific_qna.html', 'whitepaper.html']

for hfn in html_files:
    hfp = os.path.join(base, hfn)
    if not os.path.exists(hfp): continue
    with open(hfp, 'r', encoding='utf-8', errors='ignore') as f:
        hcontent = f.read()
    
    orig = hcontent
    
    # 1. Replace logo img tag style with class="nav-logo-responsive"
    hcontent = re.sub(
        r'<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>',
        logo_tag,
        hcontent
    )
    
    # 2. Ensure logo_css is injected in <head> if not in CSS
    if 'nav-logo-responsive' not in hcontent:
        hcontent = hcontent.replace('</head>', f'<style>{logo_css}</style>\n</head>')

    if hcontent != orig:
        with open(hfp, 'w', encoding='utf-8') as f:
            f.write(hcontent)
        print(f"Updated HTML: {hfn}")

print("DONE!")
