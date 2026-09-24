import os, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Load Base64 strings
with open(os.path.join(base, 'Bhaa_transparent.png'), 'rb') as f:
    b64_light = base64.b64encode(f.read()).decode('utf-8')

with open(os.path.join(base, 'Bhaa_transparent_darkmode.png'), 'rb') as f:
    b64_dark = base64.b64encode(f.read()).decode('utf-8')

logo_dark_sim_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_dark}" alt="Nilus Lab" class="nav-logo-responsive" style="height:32px!important;max-height:32px!important;width:auto;display:block;transform:none!important;"></a>'

with open(os.path.join(base, 'index.html'), 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

orig = content

# Replace the nested <a> tags in branding status pill around line 2621
old_sim_brand_pattern = r'<a href="profile\.html"[^>]*>\s*<a href="index\.html"[^>]*><img src="data:image/png;base64,[^"]+"[^>]*></a>\s*</a>'
content = re.sub(old_sim_brand_pattern, logo_dark_sim_tag, content, flags=re.DOTALL)

# Also match single nested a tag if present
old_sim_brand_pattern2 = r'<a href="profile\.html"[^>]*>\s*<a href="index\.html"[^>]*><img src="[^"]*"[^>]*></a>'
content = re.sub(old_sim_brand_pattern2, logo_dark_sim_tag, content, flags=re.DOTALL)

if content != orig:
    with open(os.path.join(base, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed simulation header logo in index.html!")
else:
    print("NO MATCH - Let me inspect line 2620-2625 of index.html")
