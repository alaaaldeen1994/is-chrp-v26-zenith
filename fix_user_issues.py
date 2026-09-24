import os, re, base64

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# Load Base64 strings for transparent light and dark logos
with open(os.path.join(base, 'Bhaa_transparent.png'), 'rb') as f:
    b64_light = base64.b64encode(f.read()).decode('utf-8')

with open(os.path.join(base, 'Bhaa_transparent_darkmode.png'), 'rb') as f:
    b64_dark = base64.b64encode(f.read()).decode('utf-8')

logo_light_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_light}" alt="Nilus Lab" class="nav-logo-responsive" style="height:32px!important;max-height:32px!important;width:auto;display:block;transform:none!important;"></a>'

logo_dark_tag = f'<a href="index.html" style="display:flex;align-items:center;text-decoration:none;flex-shrink:0;"><img src="data:image/png;base64,{b64_dark}" alt="Nilus Lab" class="nav-logo-responsive" style="height:32px!important;max-height:32px!important;width:auto;display:block;transform:none!important;"></a>'

# 1. FIX technical_catalog.html SIDEBAR LOGO
tc_path = os.path.join(base, 'technical_catalog.html')
with open(tc_path, 'r', encoding='utf-8', errors='ignore') as f:
    tc_content = f.read()

tc_orig = tc_content

# Replace the sidebar header in technical_catalog.html
old_tc_brand = r'<div class="flex items-center gap-3 mb-2">\s*<div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">\s*<i data-lucide="zap" class="w-5 h-5 text-white"></i>\s*</div>\s*<h1 class="text-xl font-black tracking-tighter text-white uppercase">Zenith <span class="text-blue-500">v31\.0 GOLD</span></h1>\s*</div>'

new_tc_brand = f'<div class="flex items-center gap-3 mb-2">{logo_dark_tag}</div>'

tc_content = re.sub(old_tc_brand, new_tc_brand, tc_content)

if tc_content != tc_orig:
    with open(tc_path, 'w', encoding='utf-8') as f:
        f.write(tc_content)
    print("SUCCESS: Updated technical_catalog.html sidebar logo!")
else:
    print("WARNING: technical_catalog.html brand pattern not matched")

# 2. FIX index.html PROMPT VIEW LOGO & AUTH GUARD
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

# Replace the top left prompt view logo (lines 1437-1446)
old_prompt_logo = r'<a href="profile\.html" style="display:flex;align-items:center;gap:8px;text-decoration:none;cursor:pointer;">\s*<div style="width:28px;height:28px;background:#1a1a1a;border-radius:50%;display:flex;align-items:center;justify-content:center;">\s*<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f8f8f6" stroke-width="2">\s*<circle cx="12" cy="12" r="5"/>\s*<path d="M12 2v3M12 19v3M2 12h3M19 12h3M4\.93 4\.93l2\.12 2\.12M16\.95 16\.95l2\.12 2\.12M4\.93 19\.07l2\.12-2\.12M16\.95 7\.05l2\.12-2\.12"/>\s*</svg>\s*</div>\s*<span style="color:#1a1a1a;font-weight:600;font-size:14px;letter-spacing:-0\.01em;font-family:\'Inter\',\'Segoe UI\',sans-serif;">Nilus Lab</span>\s*<span style="font-size:11px;color:#9b9b9b;font-weight:400;font-family:\'Inter\',\'Segoe UI\',sans-serif;">Zenith v31</span>\s*</a>'

idx_content = re.sub(old_prompt_logo, logo_light_tag, idx_content)

# Add Auth Guard check in runDiscovery() to require sign-in before analysis/chat
if 'async function runDiscovery()' in idx_content and 'if (!window._isAuthenticated)' not in idx_content.split('async function runDiscovery()')[1][:300]:
    idx_content = idx_content.replace(
        'async function runDiscovery() {',
        'async function runDiscovery() {\n    if (!window._isAuthenticated) {\n        localStorage.setItem("auth_redirect", "discovery");\n        window.location.href = "login.html";\n        return;\n    }'
    )

# Add Auth Guard check in enterSimulation() to require sign-in before entering simulation
if 'function enterSimulation()' in idx_content and 'if (!window._isAuthenticated)' not in idx_content.split('function enterSimulation()')[1][:300]:
    idx_content = idx_content.replace(
        'function enterSimulation() {',
        'function enterSimulation() {\n    if (!window._isAuthenticated) {\n        localStorage.setItem("auth_redirect", "sim");\n        window.location.href = "login.html";\n        return;\n    }'
    )

if idx_content != idx_orig:
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print("SUCCESS: Updated index.html prompt view logo and auth enforcement!")
else:
    print("WARNING: index.html prompt view pattern not matched")

print("DONE!")
