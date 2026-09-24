import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

bad_str = "<script>window.onload = function() { window.print(); };<\/script>"
fixed_str = "<' + 'script>window.onload = function() { window.print(); };<' + '/script>"

if bad_str in content:
    content = content.replace(bad_str, fixed_str)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Fixed template literal script tag in index.html!")
else:
    print("bad_str not found, checking with regex...")

res = subprocess.run(['python', 'check_inline_scripts.py'], capture_output=True, text=True, cwd=base)
print("check_inline_scripts output:")
print(res.stdout)
