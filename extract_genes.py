"""Extract gene vocabulary from 486k model for perturbation engine."""
import torch
import json

state = torch.load("models/scvi_model_486k/model.pt", map_location="cpu", weights_only=False)
var_names = list(state["var_names"])

print(f"Total genes: {len(var_names)}")
print(f"First 20: {var_names[:20]}")

# Check key markers
key_genes = [
    "POU5F1", "SOX2", "KLF4", "MYC", "TNNT2", "TTN", "PECAM1",
    "COL1A1", "CD68", "GATA4", "TBX5", "MEF2C", "MYH6", "RYR2",
    "SIRT1", "FOXO3", "TP53", "VWF", "DCN", "CD3D", "NKX2-5",
    "ACTN2", "SCN5A", "MYH7", "NANOG", "LIN28A"
]

gene_index = {}
for g in key_genes:
    if g in var_names:
        gene_index[g] = var_names.index(g)
        print(f"  FOUND: {g} at index {gene_index[g]}")
    else:
        print(f"  MISSING: {g}")

# Save full gene index for perturbation engine
with open("models/scvi_model_486k/gene_index.json", "w") as f:
    json.dump({"var_names": var_names, "key_markers": gene_index}, f)

print(f"\nSaved gene_index.json ({len(var_names)} genes)")

# Check model architecture from attr_dict
if "attr_dict" in state:
    attr = state["attr_dict"]
    for k in ["n_input", "n_batch", "n_labels", "n_hidden", "n_latent", "n_layers"]:
        if k in attr:
            print(f"  {k}: {attr[k]}")
