"""
Phase 4: Compute REAL centroids from the trained scVI model.
Source: Litviňuková et al., Nature 2020 — 14 donors, real ages.

Young donors (40-55y):  H6, H7, D1, H2, H3, H5
Aged donors (65-75y):  D4, D5, D6, D7, D11

Saves: models/real_centroids.json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json
import numpy as np
import scanpy as sc
import scvi

DONOR_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5,
    "D5": 67.5, "D6": 72.5, "D7": 62.5, "D11": 62.5,
    "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5,
    "H6": 42.5, "H7": 47.5,
}

YOUNG_DONORS = [d for d, age in DONOR_AGE_MAP.items() if age <= 55]  # 40-55
AGED_DONORS  = [d for d, age in DONOR_AGE_MAP.items() if age >= 65]  # 65-75

MODEL_DIR    = "models/scvi_model_486k_real"
DATA_PATH    = "data/hca_full/heart_adult_full.h5ad"
OUT_PATH     = "models/real_centroids.json"

def main():
    print("=" * 60)
    print("Phase 4: Real Centroid Computation")
    print("=" * 60)

    if not os.path.exists(MODEL_DIR):
        raise FileNotFoundError(f"Model not found at {MODEL_DIR}. Run training first.")

    # Load model
    print(f"\n[1/4] Loading model from {MODEL_DIR}...")
    model = scvi.model.SCVI.load(MODEL_DIR)
    print("  Model loaded.")

    # Load model (saved without adata — reload data separately)
    print(f"\n[2/4] Loading training data to get embeddings...")
    import scanpy as sc
    import numpy as np

    adata = sc.read_h5ad(DATA_PATH)
    adata.raw = None  # drop raw to save memory

    # Add donor ages
    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)

    # Stratified subsample (same seed as training — reproducible)
    np.random.seed(42)
    donor_counts = adata.obs['donor_id'].value_counts()
    total = donor_counts.sum()
    SUBSAMPLE_N = 100_000
    indices = []
    for donor, count in donor_counts.items():
        n_sample = max(1, int(SUBSAMPLE_N * count / total))
        donor_idx = np.where(adata.obs['donor_id'] == donor)[0]
        chosen = np.random.choice(donor_idx, size=min(n_sample, len(donor_idx)), replace=False)
        indices.extend(chosen.tolist())
    indices = sorted(indices)
    adata = adata[indices].copy()

    # Select same HVGs used during training
    sc.pp.highly_variable_genes(adata, n_top_genes=5000, subset=True)
    print(f"  {adata.n_obs:,} cells, {adata.n_vars} genes")

    # Setup adata for the loaded model
    scvi.model.SCVI.setup_anndata(adata)
    model.adata = adata

    # Get latent representations
    print(f"\n[3/4] Computing latent embeddings...")
    latent = model.get_latent_representation()
    print(f"  Latent shape: {latent.shape}")  # (n_cells, 20)

    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP)

    # Compute centroids
    print(f"\n[4/4] Computing centroids...")
    print(f"  Young donors ({YOUNG_DONORS}): age <= 55")
    print(f"  Aged donors  ({AGED_DONORS}): age >= 65")

    young_mask = adata.obs["donor_id"].isin(YOUNG_DONORS).values
    aged_mask  = adata.obs["donor_id"].isin(AGED_DONORS).values

    young_centroid = latent[young_mask].mean(axis=0)
    aged_centroid  = latent[aged_mask].mean(axis=0)

    young_n = int(young_mask.sum())
    aged_n  = int(aged_mask.sum())

    print(f"  Young cells: {young_n:,}")
    print(f"  Aged cells:  {aged_n:,}")

    # Rejection vector: aged → young direction
    rejuvenation_vector = young_centroid - aged_centroid
    magnitude = float(np.linalg.norm(rejuvenation_vector))
    print(f"  Rejuvenation vector magnitude: {magnitude:.4f}")

    # Save
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    result = {
        "source": "Litvinukova et al., Nature 2020",
        "model": MODEL_DIR,
        "n_latent_dims": int(latent.shape[1]),
        "young": {
            "donors": YOUNG_DONORS,
            "age_range": "40-55 years",
            "n_cells": young_n,
            "centroid": young_centroid.tolist()
        },
        "aged": {
            "donors": AGED_DONORS,
            "age_range": "65-75 years",
            "n_cells": aged_n,
            "centroid": aged_centroid.tolist()
        },
        "rejuvenation_vector": {
            "direction": rejuvenation_vector.tolist(),
            "magnitude": magnitude
        }
    }
    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  Saved centroids to {OUT_PATH}")
    print("\n" + "=" * 60)
    print("CENTROID COMPUTATION COMPLETE")
    print(f"  Young centroid: {len(YOUNG_DONORS)} donors, {young_n:,} cells")
    print(f"  Aged centroid:  {len(AGED_DONORS)} donors, {aged_n:,} cells")
    print(f"  Rejuvenation vector magnitude: {magnitude:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
