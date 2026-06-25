import json
import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
cell_type_path = os.path.join(base_dir, "models", "cell_type_genes.json")
real_ip_path = os.path.join(base_dir, "models", "real_ip_genes_full.json")

print("--- Inspecting cell_type_genes.json ---")
if os.path.exists(cell_type_path):
    with open(cell_type_path, 'r', encoding='utf-8') as f:
        ct_data = json.load(f)
    print("Keys in cell_types:", list(ct_data.get("cell_types", {}).keys()))
    for ct_key, data in ct_data.get("cell_types", {}).items():
        print(f"\nCell Type: {data.get('cell_type')} ({ct_key})")
        print(f"  Total cells: {data.get('n_cells'):,}")
        print(f"  Young cells: {data.get('n_young'):,}")
        print(f"  Aged cells: {data.get('n_aged'):,}")
        print(f"  Age delta years: {data.get('age_delta_years')}")
        pro_genes = data.get("pro_rejuvenation_genes", [])
        aging_genes = data.get("aging_marker_genes", [])
        print(f"  Pro-rejuvenation genes count: {len(pro_genes)}")
        if pro_genes:
            print(f"  Top 5 Pro-rejuv: {[(g.get('gene'), round(g.get('correlation'), 4)) for g in pro_genes[:5]]}")
        print(f"  Aging marker genes count: {len(aging_genes)}")
        if aging_genes:
            print(f"  Top 5 Aging markers: {[(g.get('gene'), round(g.get('correlation'), 4)) for g in aging_genes[:5]]}")
else:
    print("cell_type_genes.json does not exist!")

print("\n--- Inspecting real_ip_genes_full.json ---")
if os.path.exists(real_ip_path):
    with open(real_ip_path, 'r', encoding='utf-8') as f:
        ip_data = json.load(f)
    print("Keys in real_ip_genes_full.json:", list(ip_data.keys()))
    pro_genes = ip_data.get("pro_rejuvenation_genes", [])
    aging_genes = ip_data.get("aging_marker_genes", [])
    print(f"  Pro-rejuvenation genes count: {len(pro_genes)}")
    if pro_genes:
        print(f"  Top 5 Pro-rejuv: {[(g.get('gene_symbol'), round(g.get('correlation'), 4)) for g in pro_genes[:5]]}")
    print(f"  Aging marker genes count: {len(aging_genes)}")
    if aging_genes:
        print(f"  Top 5 Aging markers: {[(g.get('gene_symbol'), round(g.get('correlation'), 4)) for g in aging_genes[:5]]}")
else:
    print("real_ip_genes_full.json does not exist!")
