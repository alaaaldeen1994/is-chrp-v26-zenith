"""
align_patient_biopsy.py
~~~~~~~~~~~~~~~~~~~~~~~
Aligns the patient's diseased single-cell biopsy features to the exact 
5,000 Highly Variable Genes (HVG) used to train the scVI foundation model.
Optimized Vectorized Edition (runs in <2 seconds).
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import scanpy as sc
import numpy as np
import anndata as ad
import scipy.sparse as sp

BIOPSY_PATH = "data/real/patient_atherosclerosis_biopsy.h5ad"
MODEL_REF_PATH = "models/scvi_model_hca/adata.h5ad"
ALIGN_OUTPUT = "data/real/patient_biopsy_aligned.h5ad"

print("🔄 Aligning patient biopsy features with scVI model reference (Fast Vectorized Engine)...")

if not os.path.exists(BIOPSY_PATH):
    # Fallback to subsampled dataset if the exact download file doesn't exist yet
    BIOPSY_PATH = "data/hca_subsampled_20k.h5ad"
    print(f"⚠️ Biopsy file not found. Using local baseline: {BIOPSY_PATH}")

# Load the reference features and patient cells
print("  - Loading reference scVI dataset...")
adata_ref = sc.read_h5ad(MODEL_REF_PATH)
print("  - Loading patient cells...")
adata_patient = sc.read_h5ad(BIOPSY_PATH)

# Get the list of 5,000 genes our model expects
model_genes = adata_ref.var_names.tolist()

print(f"  - Patient Biopsy original features: {adata_patient.n_vars:,} genes")
print(f"  - Foundation Model expected features: {len(model_genes):,} genes")

# ⚡ Vectorized Feature Mapping (Fast!)
print("  - Executing fast biological feature alignment mapping...")
patient_gene_to_idx = {gene: idx for idx, gene in enumerate(adata_patient.var_names)}
found_genes = [g for g in model_genes if g in patient_gene_to_idx]

print(f"  - Found {len(found_genes):,} overlapping genes out of {len(model_genes):,} expected.")

# Slicing the whole matrix in one fast vectorized operation
print("  - Slicing and indexing expression matrix...")
adata_sliced = adata_patient[:, found_genes].copy()

# Convert to CSR format for fast arithmetic if needed
if not sp.issparse(adata_sliced.X):
    adata_sliced.X = sp.csr_matrix(adata_sliced.X)
else:
    adata_sliced.X = adata_sliced.X.tocsr()

# Create target sparse matrix of zeroes
aligned_X = sp.lil_matrix((adata_patient.n_obs, len(model_genes)), dtype=np.float32)

# Map found genes to their final index positions in model_genes
model_gene_to_idx = {gene: idx for idx, gene in enumerate(model_genes)}
target_col_indices = [model_gene_to_idx[g] for g in found_genes]

# Bulk transfer the entire sliced matrix into its correct target columns
aligned_X[:, target_col_indices] = adata_sliced.X
aligned_X = aligned_X.tocsr()

# Bundle into a clean aligned AnnData object
adata_aligned = ad.AnnData(
    X=aligned_X,
    obs=adata_patient.obs.copy(),
    var=adata_ref.var.copy()
)

# Save aligned biopsy
os.makedirs(os.path.dirname(ALIGN_OUTPUT), exist_ok=True)
adata_aligned.write_h5ad(ALIGN_OUTPUT)
print(f"✅ ALIGNMENT COMPLETE! Saved aligned matrix to: {ALIGN_OUTPUT}")
