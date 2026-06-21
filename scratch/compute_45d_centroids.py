import os
import sys
import json
import numpy as np
import scanpy as sc
import torch

sys.stdout.reconfigure(encoding='utf-8')

import scvi
from scvi.model import SCVI

model_dir = "models/zenith_foundation_v1"
data_path = "data/hca_subsampled_20k.h5ad"

if not os.path.exists(model_dir):
    print(f"Error: {model_dir} not found")
    sys.exit(1)

if not os.path.exists(data_path):
    print(f"Error: {data_path} not found")
    sys.exit(1)

print("Reading expected genes from gene_index.json...")
gene_index_path = os.path.join(model_dir, "gene_index.json")
with open(gene_index_path, "r") as f:
    gene_data = json.load(f)
    expected_vars = gene_data["var_names"]
print(f"Model expects {len(expected_vars)} genes.")

print("Loading dataset...")
adata = sc.read_h5ad(data_path)
print(f"Loaded adata with shape: {adata.shape}")

# Ensure all expected genes are in adata
missing_genes = [g for g in expected_vars if g not in adata.var_names]
if missing_genes:
    print(f"Warning: {len(missing_genes)} genes are missing from the dataset. Aligning with zero-filling...")
    import pandas as pd
    from scipy.sparse import csr_matrix, hstack
    
    expr_data_list = []
    for gene in expected_vars:
        if gene in adata.var_names:
            # Check if there is a 'counts' layer or if we use .X
            if "counts" in adata.layers:
                col_idx = adata.var_names.get_loc(gene)
                expr_data_list.append(adata.layers["counts"][:, col_idx].reshape(-1, 1))
            else:
                expr_data_list.append(adata[:, gene].X)
        else:
            zero_col = csr_matrix((adata.n_obs, 1), dtype=np.float32)
            expr_data_list.append(zero_col)
            
    new_X = hstack(expr_data_list).tocsr()
    adata_aligned = sc.AnnData(
        X=new_X,
        obs=adata.obs.copy(),
        var=pd.DataFrame(index=expected_vars)
    )
    adata = adata_aligned
else:
    print("All expected genes are present in the dataset. Subsetting...")
    # If the original has a 'counts' layer, we should subset that as well
    if "counts" in adata.layers:
        print("Using original counts layer...")
        adata_aligned = sc.AnnData(
            X=adata[:, expected_vars].layers["counts"].copy(),
            obs=adata.obs.copy(),
            var=pd.DataFrame(index=expected_vars)
        )
        adata = adata_aligned
    else:
        adata = adata[:, expected_vars].copy()

# Critical: set counts layer as expected by the model
print("Setting adata.layers['counts']...")
adata.layers["counts"] = adata.X.copy()

print(f"Aligned adata shape: {adata.shape}")

print("Re-loading model with aligned adata...")
# Setup anndata
SCVI.setup_anndata(adata, layer="counts")
model = SCVI.load(model_dir, adata=adata)
print("Model loaded successfully with aligned data.")

print("Computing latent representations...")
latent = model.get_latent_representation()
print(f"Latent representation shape: {latent.shape}")

# Group by cell type and compute centroids
cell_types = adata.obs["cell_type"].unique()
centroids = {}

for ct in cell_types:
    if ct == "doublets" or ct == "NotAssigned":
        continue
    mask = adata.obs["cell_type"] == ct
    ct_cells = latent[mask]
    if len(ct_cells) > 0:
        centroid = ct_cells.mean(axis=0)
        centroids[str(ct)] = centroid.tolist()
        print(f"Cell Type: {ct:<30} | Cells: {len(ct_cells):<6} | Centroid norm: {np.linalg.norm(centroid):.4f}")

# Save to a temporary json
out_path = "models/cell_type_centroids_45d.json"
with open(out_path, "w") as f:
    json.dump({
        "source": "HCA Subsampled 20k, zenith_foundation_v1",
        "n_latent_dims": latent.shape[1],
        "centroids": centroids
    }, f, indent=2)

print(f"Saved computed centroids to {out_path}")
