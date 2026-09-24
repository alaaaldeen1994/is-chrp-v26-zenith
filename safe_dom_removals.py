import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
js_path = os.path.join(base, 'js', 'script.js')

with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Make DOM removals safe
content = content.replace("setTimeout(() => div.remove(), 3000);", "setTimeout(() => { if (div) { if (div.remove) div.remove(); else if (div.parentNode) div.parentNode.removeChild(div); } }, 3000);")
content = content.replace("loadingDiv.remove();", "if (loadingDiv) { if (loadingDiv.remove) loadingDiv.remove(); else if (loadingDiv.parentNode) loadingDiv.parentNode.removeChild(loadingDiv); }")
content = content.replace("lockEl.remove();", "if (lockEl) { if (lockEl.remove) lockEl.remove(); else if (lockEl.parentNode) lockEl.parentNode.removeChild(lockEl); }")
content = content.replace("a.remove();", "if (a) { if (a.remove) a.remove(); else if (a.parentNode) a.parentNode.removeChild(a); }")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Updated DOM removal calls for cross-browser safety!")

res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
