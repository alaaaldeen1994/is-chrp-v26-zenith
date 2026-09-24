import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

target_pages = [
    'evidence.html', 'scientific_qna.html', 'whitepaper.html', 'trials.html', 'structure.html', 'technical_catalog.html'
]

for fname in target_pages:
    fp = os.path.join(base, fname)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    print(f"=== {fname} ===")
    for i, line in enumerate(lines):
        if 'NILUS' in line or 'brand' in line.lower() or 'logo' in line.lower():
            if any(k in line.lower() for k in ['span', 'div', 'img', 'header', 'nav']):
                start = max(0, i-3)
                end = min(len(lines), i+4)
                print(f"--- Line {i+1} ---")
                for j in range(start, end):
                    print(f"  {j+1}: {lines[j].strip()[:140]}")
