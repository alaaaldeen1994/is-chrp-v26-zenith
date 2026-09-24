import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Add explicit window assignments at top and bottom of definitions
attach_code = """
// ── EXPLICIT GLOBAL WINDOW BINDINGS FOR CROSS-MODULE ACCESS ──
if (typeof window !== 'undefined') {
    window.CONFIG = typeof CONFIG !== 'undefined' ? CONFIG : window.CONFIG;
    window.BiosimRenderer = typeof BiosimRenderer !== 'undefined' ? BiosimRenderer : window.BiosimRenderer;
    window.BiosimEngine = typeof BiosimEngine !== 'undefined' ? BiosimEngine : window.BiosimEngine;
    window.BiosimBridge = typeof BiosimBridge !== 'undefined' ? BiosimBridge : window.BiosimBridge;
    window.BiosimUI = typeof BiosimUI !== 'undefined' ? BiosimUI : window.BiosimUI;
    window.BiosimStore = typeof BiosimStore !== 'undefined' ? BiosimStore : window.BiosimStore;
    window.BiosimLab = typeof BiosimLab !== 'undefined' ? BiosimLab : window.BiosimLab;
    window.BiosimHistory = typeof BiosimHistory !== 'undefined' ? BiosimHistory : window.BiosimHistory;
    window.Agent = typeof Agent !== 'undefined' ? Agent : window.Agent;
}
"""

if "window.BiosimEngine = BiosimEngine;" not in content:
    content += attach_code
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Appended explicit window global bindings to js/script.js!")
else:
    print("Already attached to window")

# Also check index.html enterSimulation and replace 'typeof BiosimEngine' with 'typeof window.BiosimEngine !== "undefined" ? window.BiosimEngine : (typeof BiosimEngine !== "undefined" ? BiosimEngine : undefined)'
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_content = idx_content.replace("if (typeof BiosimEngine !== 'undefined')", "const engine = window.BiosimEngine || (typeof BiosimEngine !== 'undefined' ? BiosimEngine : null);\n        if (engine)")
idx_content = idx_content.replace("BiosimEngine.", "engine.")

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(idx_content)

print("Updated index.html enterSimulation to handle engine references safely!")
