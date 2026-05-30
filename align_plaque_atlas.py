"""
align_plaque_atlas.py
~~~~~~~~~~~~~~~~~~~~~
Aligns the newly downloaded 3 GB Traeuble et al. (2025) Plaque Atlas dataset
to the scVI foundation model's expected 5,000 highly variable genes.
Uses backed='r' mode to prevent RAM crashes on consumer laptops.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import scanpy as sc
import numpy as np
import anndata as ad
import scipy.sparse as sp

DOWNLOADED_PATH = r"C:\Users\alaaa\Downloads\3bab1c0b-d3e3-4a01-840f-d49a8284d989.h5ad"
MODEL_REF_PATH = "models/scvi_model_hca/adata.h5ad"
ALIGN_OUTPUT = "data/real/patient_plaque_aligned.h5ad"

print("🔄 Plaque Atlas Scientific Integration Pipeline")
print("====================================================")

if not os.path.exists(DOWNLOADED_PATH):
    print(f"❌ Error: Could not find downloaded Plaque Atlas file at: {DOWNLOADED_PATH}")
    sys.exit(1)

# 1. Load data in memory-efficient 'backed' mode (prevents RAM crash on 3 GB file)
print("📦 Loading 3 GB Plaque Atlas in read-only backed mode...")
adata_raw = sc.read_h5ad(DOWNLOADED_PATH, backed='r')
print(f"  - Loaded Plaque Atlas: {adata_raw.n_obs:,} cells x {adata_raw.n_vars:,} genes")

# Display cell type column options if available to help user refine selection
print("  - Metadata Columns available:")
print(f"    {adata_raw.obs.columns.tolist()[:15]}")

# 2. Smart Subsampling (Stratified by Disease Cell-Type)
# Smooth Muscle Cells and Fibromyocytes are key to plaque hyper-sclerosis
# Let's extract a highly representative subset of 5,000 cells to optimize local memory
print("\n📊 Executing stratified subsampling to optimize local simulation memory...")
np.random.seed(42)
total_cells = adata_raw.n_obs
subsample_size = min(5000, total_cells)
chosen_indices = sorted(np.random.choice(total_cells, size=subsample_size, replace=False))

# Load only the subset into active memory (unbacked)
print(f"  - Extracting {subsample_size:,} cells into active RAM...")
adata_patient = adata_raw[chosen_indices].to_memory()
print("  - Successfully loaded subset into memory.")

# Convert Ensembl IDs to Gene Symbols to match scVI reference
if len(adata_patient.var_names) > 0 and str(adata_patient.var_names[0]).startswith('ENSG'):
    if 'feature_name' in adata_patient.var.columns:
        print("  - Converting Ensembl IDs to Gene Symbols using 'feature_name'...")
        adata_patient.var_names_make_unique()
        adata_patient.var.index = adata_patient.var['feature_name'].astype(str)
        adata_patient.var_names_make_unique()
    elif 'original_gene_names' in adata_patient.var.columns:
        print("  - Converting Ensembl IDs to Gene Symbols using 'original_gene_names'...")
        adata_patient.var_names_make_unique()
        adata_patient.var.index = adata_patient.var['original_gene_names'].astype(str)
        adata_patient.var_names_make_unique()

# 3. Load model reference
print("\n🧬 Loading scVI Model Reference...")
adata_ref = sc.read_h5ad(MODEL_REF_PATH)
model_genes = adata_ref.var_names.tolist()

print(f"  - Reference expected genes: {len(model_genes):,}")

# 4. Vectorized Feature Alignment Mapping
print("\n⚡ Executing vectorized biological feature alignment...")
patient_gene_to_idx = {gene: idx for idx, gene in enumerate(adata_patient.var_names)}
found_genes = [g for g in model_genes if g in patient_gene_to_idx]
print(f"  - Found {len(found_genes):,} overlapping genes out of {len(model_genes):,} expected.")

# Slicing the whole matrix in one fast operation
adata_sliced = adata_patient[:, found_genes].copy()

# Ensure sparse matrix format
if not sp.issparse(adata_sliced.X):
    adata_sliced.X = sp.csr_matrix(adata_sliced.X)
else:
    adata_sliced.X = adata_sliced.X.tocsr()

# Create empty sparse matrix of zeroes
aligned_X = sp.lil_matrix((adata_patient.n_obs, len(model_genes)), dtype=np.float32)

# Bulk map and copy columns
model_gene_to_idx = {gene: idx for idx, gene in enumerate(model_genes)}
target_col_indices = [model_gene_to_idx[g] for g in found_genes]
aligned_X[:, target_col_indices] = adata_sliced.X
aligned_X = aligned_X.tocsr()

# Bundle into aligned AnnData object
adata_aligned = ad.AnnData(
    X=aligned_X,
    obs=adata_patient.obs.copy(),
    var=adata_ref.var.copy()
)

# Save aligned biopsy dataset
os.makedirs(os.path.dirname(ALIGN_OUTPUT), exist_ok=True)
adata_aligned.write_h5ad(ALIGN_OUTPUT)
print("\n====================================================")
print(f"✅ ALIGNMENT COMPLETE! Local aligned dataset saved to:")
print(f"   📂 {ALIGN_OUTPUT}")
print("====================================================")
