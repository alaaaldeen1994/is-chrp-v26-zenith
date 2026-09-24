import os, re

files_to_check = ['evidence.html', 'index.html', 'profile.html', 'technical_catalog.html', 'whitepaper.html', 'about.html', 'scientific_qna.html', 'bridge_server.py']

for fname in files_to_check:
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            if '.pdf' in line.lower() or 'journal (pdf)' in line.lower() or 'zenith_scientific_paper' in line.lower():
                print(f"{fname}:{idx}: {line.strip().encode('ascii', 'ignore').decode('ascii')}")
