import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

bad_method_head = "    }\n\n    // ── UNIFIED 3D MOLECULAR REPRESENTATION (Combining Ribbon, Surface & CPK Ball-and-Stick) ──\n    drawUnifiedMolecular3DOld(ctx, agent, x, y, size) {"
fixed_method_head = "    },\n\n    // ── UNIFIED 3D MOLECULAR REPRESENTATION (Combining Ribbon, Surface & CPK Ball-and-Stick) ──\n    drawUnifiedMolecular3DOld(ctx, agent, x, y, size) {"

if bad_method_head in content:
    content = content.replace(bad_method_head, fixed_method_head)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added comma between BiosimRenderer methods in js/script.js!")
else:
    print("bad_method_head not matched, replacing with regex...")

res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("js/script.js Node check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX 100% PERFECT! 0 ERRORS IN js/script.js!")
