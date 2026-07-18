# =============================================================================
# ZENITH PLATFORM — Fix 10: Retrain Specialist Model with Protected Ion Channels
# =============================================================================
#
# PURPOSE:
#   This script retrains scvi_model_486k_real on the 486k cell HCA dataset,
#   explicitly protecting critical cardiac ion channel genes (KCNH2, KCNJ2, SCN5A...)
#   from being filtered out during Highly Variable Gene (HVG) selection.
#
# HOW TO RUN ON COLAB:
#   1. Upload your training dataset: 'data/hca_full/heart_adult_full.h5ad'
#   2. Install required libraries:
#      !pip install scvi-tools==1.1.0 scanpy anndata
#   3. Run this script.
#   4. Download the output directory 'models/scvi_model_486k_real/' and upload
#      it to your Zenith platform deployment directory under models/.
#
# =============================================================================

import os
import json
import scanpy as sc
import scvi
import numpy as np
import pandas as pd

# Donor ages midpoint mapping
DONOR_AGE_MAP = {
    "D1":  52.5,
    "D2":  62.5,
    "D3":  57.5,
    "D4":  72.5,
    "D5":  67.5,
    "D6":  72.5,
    "D7":  62.5,
    "D11": 62.5,
    "H2":  52.5,
    "H3":  52.5,
    "H4":  57.5,
    "H5":  52.5,
    "H6":  42.5,
    "H7":  47.5,
}

DATA_PATH = "data/hca_full/heart_adult_full.h5ad"
MODEL_DIR = "models/scvi_model_486k_real"
AGE_MAP_PATH = "models/donor_age_map.json"
SUBSAMPLE_N = 100_000

def main():
    print("=" * 60)
    print("REBUILDING REAL HCA scVI Model (Ion Channels Protected)")
    print("=" * 60)

    # 1. Load Data
    print(f"\n[1/6] Loading data from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}. Ensure your HCA .h5ad is uploaded.")
        
    adata = sc.read_h5ad(DATA_PATH)
    print(f"  Loaded {adata.n_obs:,} cells and {adata.n_vars:,} genes.")

    if adata.raw is not None:
        print("  Dropping .raw matrix to prevent memory overflow...")
        adata.raw = None

    # 2. Add Age Metadata
    print("\n[2/6] Mapping donor ages...")
    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)
    if adata.obs["donor_age"].isna().sum() > 0:
        raise ValueError("Unmapped donor IDs found. Ensure donor IDs match DONOR_AGE_MAP keys.")

    # 3. Stratified Subsample to 100k cells (safeguards memory on Colab standard GPU)
    print(f"\n[3/6] Subsampling to {SUBSAMPLE_N:,} cells stratified by donor...")
    np.random.seed(42)
    donor_counts = adata.obs['donor_id'].value_counts()
    total = donor_counts.sum()
    
    indices = []
    for donor, count in donor_counts.items():
        n_sample = max(1, int(SUBSAMPLE_N * count / total))
        donor_idx = np.where(adata.obs['donor_id'] == donor)[0]
        chosen = np.random.choice(donor_idx, size=min(n_sample, len(donor_idx)), replace=False)
        indices.extend(chosen.tolist())
    
    adata = adata[sorted(indices)].copy()
    print(f"  Subsample complete: {adata.n_obs:,} cells")

    # 4. Preprocessing and Gene Selection (The Protection Step)
    print("\n[4/6] Preprocessing and selecting genes...")
    adata.X = adata.X.tocsr() if hasattr(adata.X, "tocsr") else adata.X

    # Run HVG selection to find the top 5000 highly variable genes
    print("  Calculating Highly Variable Genes...")
    sc.pp.highly_variable_genes(adata, n_top_genes=5000, subset=False)

    # Widen highly variable gene list to include critical cardiac ion channels
    protected_symbols = {
        "SCN5A", "KCNH2", "KCNQ1", "KCNJ2", "CACNA1C", "HCN4",
        "KCNA5", "KCND3", "KCNIP2", "RYR2", "SLC8A1"
    }

    # Locate gene symbol column in var metadata (usually 'gene_name' or 'feature_name')
    symbol_col = None
    for col in ["gene_name", "feature_name", "symbol"]:
        if col in adata.var.columns:
            symbol_col = col
            break

    if symbol_col is not None:
        protected_ensembl = []
        for ens_id, symbol in zip(adata.var.index, adata.var[symbol_col]):
            if str(symbol).upper() in protected_symbols:
                protected_ensembl.append(ens_id)
                adata.var.loc[ens_id, "highly_variable"] = True
                
        print(f"  Successfully protected {len(protected_ensembl)} ion channel genes from filtering:")
        for idx in protected_ensembl:
            print(f"    - {adata.var.loc[idx, symbol_col]} ({idx})")
    else:
        print("  WARNING: No gene symbol column found in adata.var. Proceeding with standard HVG list.")

    # Now subset the AnnData to keep only the highly variable (and protected) genes
    adata = adata[:, adata.var["highly_variable"]].copy()
    print(f"  Final model vocabulary size: {adata.n_vars} genes")

    # 5. Train scVI
    print("\n[5/6] Training scVI model...")
    scvi.model.SCVI.setup_anndata(adata)
    model = scvi.model.SCVI(adata, n_latent=20, n_layers=2)
    model.train(max_epochs=100)

    # 6. Save Model & Configs
    print(f"\n[6/6] Saving outputs to {MODEL_DIR}...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_DIR, overwrite=True)

    # Export a clean gene index to models/scvi_model_486k_real/gene_index.json
    gene_index = {"var_names": adata.var_names.tolist()}
    with open(os.path.join(MODEL_DIR, "gene_index.json"), "w") as f:
        json.dump(gene_index, f, indent=2)

    with open(AGE_MAP_PATH, "w") as f:
        json.dump(DONOR_AGE_MAP, f, indent=2)

    print("\n" + "=" * 60)
    print("SUCCESS: REBUILT MODEL READY FOR EXPORT")
    print(f"  Output path: {MODEL_DIR}")
    print("  Make sure to upload this directory to your production server.")
    print("=" * 60)

if __name__ == "__main__":
    main()
