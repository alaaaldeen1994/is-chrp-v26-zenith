import os
import sys

# Reconfigure stdout to use utf-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
summary_path = os.path.join(base_dir, "SCIENTIFIC_SUMMARY.md")

print("\n--- SCIENTIFIC_SUMMARY.md ---")
if os.path.exists(summary_path):
    with open(summary_path, 'r', encoding='utf-8') as f:
        content = f.read()
    safe_content = content.encode('ascii', 'replace').decode('ascii')
    print(safe_content)
else:
    print("SCIENTIFIC_SUMMARY.md not found")
