import re
import os

files_to_check = [
    "js/script.js",
    "bridge_server.py"
]

pattern = re.compile(r'\b5,000\b|\b5000\b')

for rel_path in files_to_check:
    abs_path = os.path.abspath(rel_path)
    if not os.path.exists(abs_path):
        print(f"File not found: {abs_path}")
        continue
    
    print(f"\n=== Searching in {rel_path} ===")
    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if pattern.search(line):
                print(f"Line {idx}: {line.strip()}")
