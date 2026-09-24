import os, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

with open(os.path.join(base, 'Bhaa_transparent_darkmode.png'), 'rb') as f:
    b64_dark = base64.b64encode(f.read()).decode('utf-8')

logo_sim_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_dark}" alt="Nilus Lab" style="height:28px!important;max-height:28px!important;width:auto;display:block;transform:none!important;"></a>'

with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

orig = content

# Replace the simulation logo tag inside #architect-layout branding status pill
pattern = r'(<!-- 1\. BRANDING & STATUS PILL -->[\s\S]*?<div class="flex items-center gap-4">\s*)<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>'

content = re.sub(pattern, r'\1' + logo_sim_tag, content)

if content != orig:
    with open(os.path.join(base, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Tuned simulation logo height to 28px in index.html!")
else:
    print("NO CHANGE")
