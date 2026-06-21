import os
import json
import numpy as np
import scanpy as sc
import scvi

def main():
    print("=" * 70)
    print("Zenith v29.0 IP GENE DISCOVERY (2M Cells, 5858 Genes)")
    print("=" * 70)
    
    # Paths (adjust if running in Colab)
    MODEL_DIR = "models/zenith_foundation_v1"
    DATA_PATH = "data/hca_full/heart_adult_full.h5ad" # Needs to be the 2M cell dataset
    OUT_PATH = "models/v29_ip_genes.json"
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Could not find raw data at {DATA_PATH}.")
        print("Please run this script in your Colab environment where the 2M cell dataset exists.")
        return

    print("\n[1/4] Loading HCA Data...")
    adata = sc.read_h5ad(DATA_PATH)
    # Ensure it's subsampled or processed similarly to training
    
    print("\n[2/4] Loading Zenith v29.0 Foundation Model...")
    # Setup adata based on the training covariates (disease, cell_type, dataset_id, donor_id, etc.)
    scvi.model.SCVI.setup_anndata(
        adata,
        layer="counts",
        categorical_covariate_keys=["dataset_id", "disease", "cell_type", "donor_id"],
        continuous_covariate_keys=[]
    )
    model = scvi.model.SCVI.load(MODEL_DIR, adata=adata)
    
    print("\n[3/4] Computing Latent Embeddings & Disease Vector...")
    latent = model.get_latent_representation()
    
    # Example: Calculate transition vector from "dilated cardiomyopathy" to "normal"
    normal_mask = adata.obs['disease'] == 'normal'
    disease_mask = adata.obs['disease'] == 'dilated cardiomyopathy'
    
    normal_vec = latent[normal_mask].mean(axis=0)
    disease_vec = latent[disease_mask].mean(axis=0)
    
    rejuv_vec = normal_vec - disease_vec
    
    print("\n[4/4] Identifying Top Target Genes (IP)...")
    rejuv_unit = rejuv_vec / (np.linalg.norm(rejuv_vec) + 1e-10)
    cell_scores = latent @ rejuv_unit
    
    # Correlate cell scores with raw gene expressions
    import scipy.sparse as sp
    X = adata.X
    if sp.issparse(X):
        X = X.toarray()
    
    gene_names = adata.var_names.tolist()
    gene_correlations = np.zeros(X.shape[1])
    
    cell_scores_norm = (cell_scores - cell_scores.mean()) / (cell_scores.std() + 1e-10)
    
    for i in range(X.shape[1]):
        g = X[:, i]
        g_norm = (g - g.mean()) / (g.std() + 1e-10)
        gene_correlations[i] = float(np.dot(cell_scores_norm, g_norm) / len(cell_scores_norm))
        
    pro_rejuv_idx = np.argsort(gene_correlations)[::-1][:50] # Top 50 upregulated for normalization
    disease_marker_idx = np.argsort(gene_correlations)[:50]  # Top 50 downregulated (disease markers)
    
    pro_rejuv_genes = [{"gene": gene_names[i], "correlation": round(float(gene_correlations[i]), 4)} for i in pro_rejuv_idx]
    disease_marker_genes = [{"gene": gene_names[i], "correlation": round(float(gene_correlations[i]), 4)} for i in disease_marker_idx]
    
    result = {
        "source": "Zenith v29.0 Foundation Model",
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "target_transition": "dilated cardiomyopathy -> normal",
        "pro_rejuvenation_genes": pro_rejuv_genes,
        "disease_marker_genes": disease_marker_genes
    }
    
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"\n✅ IP Extraction Complete! Saved {len(pro_rejuv_genes)} target genes to {OUT_PATH}")

if __name__ == "__main__":
    main()
