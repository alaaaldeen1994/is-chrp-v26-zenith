"""
align_plaque_atlas_v2.py
~~~~~~~~~~~~~~~~~~~~~~~~
Improved alignment of the Traeuble et al. (2025) Plaque Atlas to the
scVI foundation model's 26,662 genes.

Strategy: Dual-key matching
  1. Primary match:  patient gene symbol  →  model gene symbol (var_names)
  2. Fallback match: patient Ensembl ID   →  model Ensembl ID (gene_ids-Harvard-Nuclei)
  
This rescues lncRNA / alias genes that didn't match by symbol alone, pushing
coverage from ~65% up as high as possible.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import scanpy as sc
import numpy as np
import anndata as ad
import scipy.sparse as sp

DOWNLOADED_PATH = r"C:\Users\alaaa\Downloads\3bab1c0b-d3e3-4a01-840f-d49a8284d989.h5ad"
MODEL_REF_PATH  = "models/scvi_model_hca/adata.h5ad"
ALIGN_OUTPUT    = "data/real/patient_plaque_aligned.h5ad"

print("🔄 Plaque Atlas Alignment v2 — Dual-Key Matching")
print("====================================================")

# ── 1. Load data ────────────────────────────────────────────────────────────
print("\n📦 Loading Plaque Atlas (backed mode)...")
adata_raw = sc.read_h5ad(DOWNLOADED_PATH, backed='r')
print(f"  Plaque Atlas: {adata_raw.n_obs:,} cells × {adata_raw.n_vars:,} genes")

print("\n🧬 Loading scVI Model Reference...")
adata_ref = sc.read_h5ad(MODEL_REF_PATH)
print(f"  Model reference: {adata_ref.n_vars:,} genes")

# ── 2. Build model lookup tables ─────────────────────────────────────────────
model_symbol_to_idx = {sym: i for i, sym in enumerate(adata_ref.var_names)}

# Build Ensembl→model-index map from Harvard-Nuclei column (most complete)
model_ensembl_col = 'gene_ids-Harvard-Nuclei'
model_ensembl_to_idx = {}
for i, ensembl in enumerate(adata_ref.var[model_ensembl_col]):
    if isinstance(ensembl, str) and ensembl.startswith('ENSG'):
        model_ensembl_to_idx[ensembl] = i

print(f"  Model Ensembl ID lookup built: {len(model_ensembl_to_idx):,} entries")

# ── 3. Subsample ─────────────────────────────────────────────────────────────
print("\n📊 Subsampling 5,000 representative cells...")
np.random.seed(42)
chosen = sorted(np.random.choice(adata_raw.n_obs, size=min(5000, adata_raw.n_obs), replace=False))
adata_patient = adata_raw[chosen].to_memory()
print(f"  Loaded {adata_patient.n_obs:,} cells into RAM")

# Original Ensembl IDs are the var_names before renaming
patient_ensembl_ids  = list(adata_patient.var_names)          # ENSG…
patient_symbols      = list(adata_patient.var['feature_name'].astype(str))

# ── 4. Dual-key alignment ────────────────────────────────────────────────────
print("\n⚡ Executing dual-key gene alignment...")

# For each patient gene, find its column in the model matrix
patient_gene_to_model_col = {}   # patient_var_pos  →  model_col_idx

matched_by_symbol  = 0
matched_by_ensembl = 0
unmatched          = 0

for pat_pos, (ensembl_id, symbol) in enumerate(zip(patient_ensembl_ids, patient_symbols)):
    if symbol in model_symbol_to_idx:
        patient_gene_to_model_col[pat_pos] = model_symbol_to_idx[symbol]
        matched_by_symbol += 1
    elif ensembl_id in model_ensembl_to_idx:
        patient_gene_to_model_col[pat_pos] = model_ensembl_to_idx[ensembl_id]
        matched_by_ensembl += 1
    else:
        unmatched += 1

total_matched = matched_by_symbol + matched_by_ensembl
pct           = total_matched / adata_ref.n_vars * 100
print(f"  ✅ Matched by symbol:  {matched_by_symbol:,}")
print(f"  ✅ Rescued by Ensembl: {matched_by_ensembl:,}")
print(f"  ❌ Unmatched:          {unmatched:,}")
print(f"  📈 Total coverage:     {total_matched:,} / {adata_ref.n_vars:,}  ({pct:.1f}%)")

# ── 5. Build aligned matrix ───────────────────────────────────────────────────
print("\n🔧 Building aligned expression matrix...")

# Get original sparse matrix
X_patient = adata_patient.X
if not sp.issparse(X_patient):
    X_patient = sp.csr_matrix(X_patient)
else:
    X_patient = X_patient.tocsc()   # CSC for fast column slicing

n_cells       = adata_patient.n_obs
n_model_genes = adata_ref.n_vars

aligned_X = sp.lil_matrix((n_cells, n_model_genes), dtype=np.float32)

pat_positions   = list(patient_gene_to_model_col.keys())
model_positions = [patient_gene_to_model_col[p] for p in pat_positions]

for pat_col, model_col in zip(pat_positions, model_positions):
    aligned_X[:, model_col] = X_patient[:, pat_col]

aligned_X = aligned_X.tocsr()
print(f"  Matrix shape: {aligned_X.shape[0]:,} × {aligned_X.shape[1]:,}")

# ── 6. Assemble & save ────────────────────────────────────────────────────────
print("\n💾 Saving aligned dataset...")
adata_aligned = ad.AnnData(
    X   = aligned_X,
    obs = adata_patient.obs.copy(),
    var = adata_ref.var.copy()
)
# Store match stats in uns for downstream transparency
adata_aligned.uns['alignment_stats'] = {
    'matched_by_symbol':  matched_by_symbol,
    'rescued_by_ensembl': matched_by_ensembl,
    'unmatched':          unmatched,
    'total_matched':      total_matched,
    'pct_coverage':       round(pct, 2),
    'model_total_genes':  adata_ref.n_vars,
}

os.makedirs(os.path.dirname(ALIGN_OUTPUT), exist_ok=True)
adata_aligned.write_h5ad(ALIGN_OUTPUT)

print("\n====================================================")
print(f"✅ ALIGNMENT COMPLETE  →  {ALIGN_OUTPUT}")
print(f"   Coverage: {total_matched:,} / {adata_ref.n_vars:,} genes ({pct:.1f}%)")
print("====================================================")
