import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\index.html"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        start_idx = content.find("async function runDiscovery()")
        if start_idx != -1:
            lines = content[start_idx:start_idx+10000].split("\n")
            for idx in range(150, min(300, len(lines))):
                print(f"{idx+1}: {lines[idx]}")
else:
    print("index.html not found")
