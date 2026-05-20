"""Translate Ensembl IDs in real_ip_genes.json to gene symbols and save."""
import scanpy as sc, json, os

adata = sc.read_h5ad("data/hca_full/heart_adult_full.h5ad")

# Find gene symbol column
cols = adata.var.columns.tolist()
print("var columns:", cols)

if "gene_name" in cols:
    id_map = dict(zip(adata.var.index, adata.var["gene_name"]))
elif "feature_name" in cols:
    id_map = dict(zip(adata.var.index, adata.var["feature_name"]))
else:
    id_map = {}
    print("No gene name column — staying with Ensembl IDs")

with open("models/real_ip_genes.json") as f:
    data = json.load(f)

print("\n=== TOP 15 PRO-REJUVENATION GENES (UP in 40-55y donors) ===")
for g in data["pro_rejuvenation_genes"][:15]:
    symbol = id_map.get(g["gene"], g["gene"])
    print(f"  #{g['rank']:2d}  {symbol:<20} r={g['correlation']:+.4f}")

print("\n=== TOP 15 AGING MARKER GENES (UP in 65-72y donors) ===")
for g in data["aging_marker_genes"][:15]:
    symbol = id_map.get(g["gene"], g["gene"])
    print(f"  #{g['rank']:2d}  {symbol:<20} r={g['correlation']:+.4f}")

# Update json with real symbols
for g in data["pro_rejuvenation_genes"]:
    g["gene_symbol"] = id_map.get(g["gene"], g["gene"])
for g in data["aging_marker_genes"]:
    g["gene_symbol"] = id_map.get(g["gene"], g["gene"])

with open("models/real_ip_genes.json", "w") as f:
    json.dump(data, f, indent=2)
print("\nUpdated models/real_ip_genes.json with gene symbols.")
