import os, subprocess, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Extract script blocks
scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
print(f"Found {len(scripts)} inline script blocks in index.html")

temp_js = os.path.join(base, 'temp_inline_check.js')

has_error = False
for idx, s in enumerate(scripts):
    with open(temp_js, 'w', encoding='utf-8') as f:
        f.write(s)
    res = subprocess.run(['node', '-c', temp_js], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR in inline script block #{idx+1}:")
        print(res.stderr)
        has_error = True

if os.path.exists(temp_js):
    os.remove(temp_js)

if not has_error:
    print("ALL inline script blocks in index.html passed Node syntax check!")
