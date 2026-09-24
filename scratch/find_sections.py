import re

with open(r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\technical_catalog.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Section 1.7' in line or 'Section 1.6' in line or 'Section 13' in line or 'Epigenetic' in line or 'Horvath' in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
