import json
import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
cell_type_path = os.path.join(base_dir, "models", "cell_type_genes.json")
real_ip_path = os.path.join(base_dir, "models", "real_ip_genes_full.json")

print("--- Sample from cell_type_genes.json ---")
with open(cell_type_path, 'r', encoding='utf-8') as f:
    ct_data = json.load(f)
myocyte_data = ct_data["cell_types"]["regular_ventricular_cardiac_myocyte"]
print("Pro-rejuvenation gene sample (first 3):")
for g in myocyte_data["pro_rejuvenation_genes"][:3]:
    print(g)

print("\n--- Sample from real_ip_genes_full.json ---")
with open(real_ip_path, 'r', encoding='utf-8') as f:
    ip_data = json.load(f)
print("Pro-rejuvenation gene sample (first 3):")
for g in ip_data["pro_rejuvenation_genes"][:3]:
    print(g)

print("\n--- Searching bridge_server.py for Ensembl mapping logic ---")
server_path = os.path.join(base_dir, "bridge_server.py")
with open(server_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Let's find occurrences of ensembl mapping or symbols dictionary
import re
matches = re.findall(r"(def\s+\w*map\w*|def\s+\w*symbol\w*|ensembl_to_symbol|symbol_mapping|load_mapping)", code, re.IGNORECASE)
print("Found mapping-related functions/variables:", matches)

# Let's search for "ENSG" or ".get('gene')" in bridge_server.py to see how symbols are resolved
lines = code.split('\n')
for idx, line in enumerate(lines):
    if "ensembl" in line.lower() and ("map" in line.lower() or "dict" in line.lower() or "load" in line.lower()):
        print(f"L{idx+1}: {line.strip()}")
