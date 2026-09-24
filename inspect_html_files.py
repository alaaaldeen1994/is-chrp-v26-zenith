import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
html_files = glob.glob(os.path.join(base, '*.html'))

with open(os.path.join(base, 'Bhaa_tight.png'), 'rb') as f:
    import base64
    b64 = base64.b64encode(f.read()).decode('utf-8')

logo_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64}" alt="Nilus Lab" style="height:52px;width:auto;display:block;transition:opacity 0.2s;" onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1"></a>'

for filepath in sorted(html_files):
    fname = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check if this file has any logo or header branding
    has_base64 = 'data:image/png;base64,' in content
    has_nilus = 'NILUS' in content or 'nilus' in content
    has_nav = '<nav' in content or 'nav-' in content
    
    print(f"File: {fname:35s} | base64_logo: {has_base64} | nilus: {has_nilus} | nav: {has_nav}")
