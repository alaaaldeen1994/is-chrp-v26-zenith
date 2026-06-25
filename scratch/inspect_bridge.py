import os
import sys

# Reconfigure stdout to use utf-8 to avoid CP1252 errors on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

server_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\bridge_server.py"

with open(server_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

search_terms = ["cell_type_genes.json", "real_ip_genes_full.json", "/api/gpt-discovery", "/api/discovery", "class CellType", "class Model"]

print("--- Searching bridge_server.py ---")
for term in search_terms:
    print(f"\nSearching for: {term}")
    found = False
    for idx, line in enumerate(lines):
        if term in line:
            found = True
            safe_line = line.strip().encode('ascii', 'replace').decode('ascii')
            print(f"L{idx+1}: {safe_line}")
            # Print 5 lines before and 20 lines after for context
            start = max(0, idx - 5)
            end = min(len(lines), idx + 25)
            print("--- Context ---")
            for c_idx in range(start, end):
                prefix = "-> " if c_idx == idx else "   "
                raw_line = lines[c_idx].rstrip()
                safe_raw_line = raw_line.encode('ascii', 'replace').decode('ascii')
                print(f"{prefix}L{c_idx+1}: {safe_raw_line}")
            print("----------------")
    if not found:
        print("Not found.")
