import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

content = content.replace("# Hydrogen (White)", "// Hydrogen (White)")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(content)

res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("🎉 SYNTAX 100% PERFECT! 0 errors in js/script.js!")
