# =============================================================================
# ZENITH PLATFORM — Fix 1: Compute Real Cell-Type Centroids
# =============================================================================
#
# PURPOSE:
#   This notebook computes the mean latent representation (centroid) for each
#   annotated cell type in the scvi_model_486k_real training dataset.
#   The output file (cell_type_centroids.json) is required by perturbation_engine.py
#   to perform real latent-space arithmetic simulations.
#
# WHEN TO RUN:
#   Run this once on Google Colab (GPU recommended but not required).
#   After completion, download cell_type_centroids.json and place it at:
#       models/cell_type_centroids.json
#   in your Zenith project root directory, then redeploy.
#
# WHAT YOU NEED:
#   - The scvi_model_486k_real/ model directory (from your project)
#   - The AnnData file used during training (heart_adult_full.h5ad or equivalent)
#     This must have a 'cell_type' column in adata.obs
#
# WHAT IT PRODUCES:
#   cell_type_centroids.json — a JSON dictionary where:
#     - Each key is a cell type name (e.g. "Cardiomyocyte", "Fibroblast")
#     - Each value is a list of 20 floats (the mean latent position for that type)
#   All vectors are exactly 20-dimensional (matching scvi_model_486k_real n_latent=20)
#
# =============================================================================


# ── CELL 1: Install dependencies ─────────────────────────────────────────────
# Run this cell first. Takes 2-3 minutes on Colab.

"""
!pip install scvi-tools==1.1.0 anndata scanpy
"""


# ── CELL 2: Upload your files to Colab ───────────────────────────────────────
# Upload two things:
#   1. The full scvi_model_486k_real/ folder (zip it first, then unzip below)
#   2. Your training AnnData file (.h5ad)
#
# Uncomment and run the lines you need:

"""
# Option A: If you have a zip of the model directory
!unzip scvi_model_486k_real.zip -d ./

# Option B: Mount Google Drive if your files are there
from google.colab import drive
drive.mount('/content/drive')
"""


# ── CELL 3: Load model and AnnData ───────────────────────────────────────────

import scvi
import anndata as ad
import numpy as np
import json
import os

# ── CONFIGURE THESE PATHS ──────────────────────────────────────────────────
MODEL_DIR  = "scvi_model_486k_real"   # path to the model folder on Colab
ADATA_PATH = "heart_adult_full.h5ad"  # path to the AnnData file on Colab
CELL_TYPE_COLUMN = "cell_type"        # column in adata.obs with cell type labels
OUTPUT_PATH = "cell_type_centroids.json"
# ──────────────────────────────────────────────────────────────────────────

print(f"Loading AnnData from: {ADATA_PATH}")
adata = ad.read_h5ad(ADATA_PATH)
print(f"  Cells: {adata.n_obs:,}  |  Genes: {adata.n_vars:,}")
print(f"  Cell type column '{CELL_TYPE_COLUMN}' has "
      f"{adata.obs[CELL_TYPE_COLUMN].nunique()} unique types:")
print(f"  {sorted(adata.obs[CELL_TYPE_COLUMN].unique().tolist())}")

print(f"\nLoading scVI model from: {MODEL_DIR}")
model = scvi.model.SCVI.load(MODEL_DIR, adata=adata)
print(f"  n_latent = {model.module.n_latent}")
print(f"  n_input  = {model.module.n_input}")


# ── CELL 4: Compute latent representations for all cells ─────────────────────
# This is the core computation. It runs a forward pass through the encoder
# for every cell in the dataset and returns the mean of the posterior (q(z|x)).
# give_mean=True returns the deterministic mean, not a stochastic sample.

print("\nComputing latent representations (give_mean=True)...")
print("This may take a few minutes for large datasets...")

Z = model.get_latent_representation(give_mean=True)

print(f"  Done. Z shape: {Z.shape}")
assert Z.shape[1] == model.module.n_latent, (
    f"Unexpected latent dim: got {Z.shape[1]}, expected {model.module.n_latent}"
)


# ── CELL 5: Compute per-cell-type centroids ───────────────────────────────────

cell_types_array = adata.obs[CELL_TYPE_COLUMN].values
unique_types = sorted(set(cell_types_array))

print(f"\nComputing centroids for {len(unique_types)} cell types...")

centroids = {}
for ct in unique_types:
    mask = cell_types_array == ct
    n_cells = mask.sum()
    centroid = Z[mask].mean(axis=0)  # shape: (n_latent,)
    centroids[ct] = centroid.tolist()
    print(f"  {ct:40s}  n={n_cells:6,}  |  "
          f"mean_abs={float(np.abs(centroid).mean()):.4f}  "
          f"norm={float(np.linalg.norm(centroid)):.4f}")

print(f"\n{len(centroids)} centroids computed.")


# ── CELL 6: Verify required cell types are present ────────────────────────────

REQUIRED_TYPES = {"Fibroblast", "Cardiomyocyte"}
missing = REQUIRED_TYPES - set(centroids.keys())

if missing:
    print(f"\n⚠️  WARNING: Required cell types missing from annotations: {missing}")
    print("   Check the CELL_TYPE_COLUMN name and its exact string values.")
    print("   Available types:")
    for ct in sorted(centroids.keys()):
        print(f"     '{ct}'")
    print("\n   If the names differ (e.g. 'cardiac muscle cell' vs 'Cardiomyocyte'),")
    print("   add a name mapping below and re-run this cell.")

    # ── OPTIONAL: Name mapping if your AnnData uses different labels ──────
    # Uncomment and edit as needed:
    # NAME_MAP = {
    #     "cardiac muscle cell": "Cardiomyocyte",
    #     "fibroblast": "Fibroblast",
    #     "endothelial cell": "Endothelial",
    # }
    # centroids = {NAME_MAP.get(k, k): v for k, v in centroids.items()}
    # ──────────────────────────────────────────────────────────────────────
else:
    print("\n✅ All required cell types present.")


# ── CELL 7: Save output ───────────────────────────────────────────────────────

with open(OUTPUT_PATH, "w") as f:
    json.dump(centroids, f, indent=2)

file_size_kb = os.path.getsize(OUTPUT_PATH) / 1024
print(f"\n✅ Saved: {OUTPUT_PATH}  ({file_size_kb:.1f} KB)")
print(f"   Contains {len(centroids)} cell types, each with "
      f"{model.module.n_latent} dimensions.")

# Verification: reload and check
with open(OUTPUT_PATH) as f:
    verification = json.load(f)

for ct, vec in verification.items():
    assert len(vec) == model.module.n_latent, (
        f"Centroid for '{ct}' has wrong length: {len(vec)}"
    )

print(f"   Verification passed: all centroids are {model.module.n_latent}-dimensional.")


# ── CELL 8: Download the file ─────────────────────────────────────────────────
# After this runs, the file will download to your computer automatically.

"""
from google.colab import files
files.download(OUTPUT_PATH)
"""

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print(f"1. Download '{OUTPUT_PATH}' from Colab")
print(f"2. Place it at:  models/cell_type_centroids.json  in your project")
print(f"3. Commit and push to Railway")
print(f"4. At next server start, PerturbationEngine will load real centroids")
print(f"   and set mode='expert' for the first time.")
print("="*60)
