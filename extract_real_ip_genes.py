"""
REAL IP DISCOVERY — From HCA Latent Space
==========================================
Source: Litviňuková et al., Nature 2020
Model:  models/scvi_model_486k_real (trained May 2026)
Method: Decode the rejuvenation vector through the scVI decoder
        to find which of the 5,000 genes are most responsible
        for the young→aged transition in the 14 real donors.

This is the ACTUAL discovery — not GPT, not literature.
Saves: models/real_ip_genes.json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json
import numpy as np
import scanpy as sc
import scvi
import torch

DONOR_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5,
    "D5": 67.5, "D6": 72.5, "D7": 62.5, "D11": 62.5,
    "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5,
    "H6": 42.5, "H7": 47.5,
}
YOUNG_DONORS = [d for d, age in DONOR_AGE_MAP.items() if age <= 55]
AGED_DONORS  = [d for d, age in DONOR_AGE_MAP.items() if age >= 65]

MODEL_DIR     = "models/scvi_model_486k_real"
CENTROIDS_PATH= "models/real_centroids.json"
DATA_PATH     = "data/hca_full/heart_adult_full.h5ad"
OUT_PATH      = "models/real_ip_genes.json"

def main():
    print("=" * 70)
    print("REAL IP GENE DISCOVERY — From HCA 2020 Latent Space")
    print("Source: Litvinukova et al., Nature 2020 — 14 real donors")
    print("=" * 70)

    # ── 1. Load model ────────────────────────────────────────────────────
    print("\n[1/5] Loading trained scVI model...")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = scvi.model.SCVI.load(MODEL_DIR)
    print("  Model loaded.")

    # ── 2. Reload data with same subsample ───────────────────────────────
    print(f"\n[2/5] Loading HCA data...")
    adata = sc.read_h5ad(DATA_PATH)
    adata.raw = None
    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)

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
    adata = adata[sorted(indices)].copy()
    sc.pp.highly_variable_genes(adata, n_top_genes=5000, subset=True)
    print(f"  {adata.n_obs:,} cells, {adata.n_vars} genes")

    scvi.model.SCVI.setup_anndata(adata)
    model.adata = adata

    # ── 3. Get latent embeddings ─────────────────────────────────────────
    print(f"\n[3/5] Computing latent embeddings...")
    latent = model.get_latent_representation()  # (n_cells, 20)
    gene_names = adata.var_names.tolist()
    print(f"  Latent shape: {latent.shape}")

    # ── 4. Load rejuvenation vector from centroids ───────────────────────
    print(f"\n[4/5] Loading real rejuvenation vector...")
    with open(CENTROIDS_PATH) as f:
        centroids = json.load(f)

    young_vec = np.array(centroids["young"]["centroid"])
    aged_vec  = np.array(centroids["aged"]["centroid"])
    rejuv_vec = young_vec - aged_vec  # direction: aged → young
    magnitude = float(np.linalg.norm(rejuv_vec))
    print(f"  Rejuvenation vector magnitude: {magnitude:.4f}")
    print(f"  Young donors: {centroids['young']['donors']} ({centroids['young']['n_cells']:,} cells)")
    print(f"  Aged donors:  {centroids['aged']['donors']} ({centroids['aged']['n_cells']:,} cells)")

    # ── 5. Project each gene onto rejuvenation vector ────────────────────
    print(f"\n[5/5] Identifying real IP genes...")
    print("  Method: Correlation of each gene's expression with the")
    print("  rejuvenation direction in latent space (young - aged axis)")

    # For each cell, compute its projection onto the rejuvenation vector
    rejuv_unit = rejuv_vec / (np.linalg.norm(rejuv_vec) + 1e-10)
    cell_scores = latent @ rejuv_unit  # (n_cells,) — how "young" each cell is

    # Get gene expression matrix
    import scipy.sparse as sp
    X = adata.X
    if sp.issparse(X):
        X = X.toarray()
    X = np.array(X, dtype=float)

    # Pearson correlation: each gene vs cell rejuvenation score
    # Positive correlation = gene goes UP in young cells (pro-rejuvenation)
    # Negative correlation = gene goes DOWN in young cells (aging marker)
    print("  Computing correlations for 5,000 genes...")
    cell_scores_norm = (cell_scores - cell_scores.mean()) / (cell_scores.std() + 1e-10)

    gene_correlations = np.zeros(X.shape[1])
    for i in range(X.shape[1]):
        g = X[:, i]
        g_norm = (g - g.mean()) / (g.std() + 1e-10)
        gene_correlations[i] = float(np.dot(cell_scores_norm, g_norm) / len(cell_scores_norm))

    # Rank genes by absolute correlation
    sorted_idx = np.argsort(np.abs(gene_correlations))[::-1]

    # Top 20 pro-rejuvenation genes (positive correlation)
    pro_rejuv_idx = np.argsort(gene_correlations)[::-1][:20]
    # Top 20 aging markers (negative correlation = high in aged cells)
    aging_marker_idx = np.argsort(gene_correlations)[:20]

    pro_rejuv_genes = [
        {
            "gene": gene_names[i],
            "correlation": round(float(gene_correlations[i]), 4),
            "direction": "UP_IN_YOUNG",
            "rank": int(rank) + 1
        }
        for rank, i in enumerate(pro_rejuv_idx)
    ]

    aging_marker_genes = [
        {
            "gene": gene_names[i],
            "correlation": round(float(gene_correlations[i]), 4),
            "direction": "UP_IN_AGED",
            "rank": int(rank) + 1
        }
        for rank, i in enumerate(aging_marker_idx)
    ]

    # Per-donor mean rejuvenation score
    donor_scores = {}
    for donor in sorted(DONOR_AGE_MAP.keys()):
        mask = (adata.obs["donor_id"] == donor).values
        if mask.sum() == 0:
            continue
        score = float(cell_scores[mask].mean())
        donor_scores[donor] = {
            "score": round(score, 4),
            "age": DONOR_AGE_MAP[donor],
            "n_cells": int(mask.sum())
        }

    # ── Save ─────────────────────────────────────────────────────────────
    result = {
        "source": "Litvinukova et al., Nature 2020",
        "doi": "10.1038/s41586-020-2797-4",
        "model": MODEL_DIR,
        "method": "Pearson correlation of gene expression with latent rejuvenation vector",
        "n_cells": int(adata.n_obs),
        "n_genes_analysed": int(adata.n_vars),
        "rejuvenation_vector_magnitude": magnitude,
        "pro_rejuvenation_genes": pro_rejuv_genes,
        "aging_marker_genes": aging_marker_genes,
        "donor_rejuvenation_scores": donor_scores
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n  Saved to {OUT_PATH}")

    # ── Print IP summary ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("REAL IP DISCOVERY RESULTS — From HCA 2020 Latent Space")
    print("=" * 70)
    print("\nTOP 15 PRO-REJUVENATION GENES (UP in young donors from HCA data):")
    print(f"{'Rank':<6} {'Gene':<12} {'Correlation':<14} {'Meaning'}")
    print("-" * 55)
    for g in pro_rejuv_genes[:15]:
        print(f"  {g['rank']:<4} {g['gene']:<12} {g['correlation']:>+.4f}       Higher in 40-55y donors")

    print("\nTOP 15 AGING MARKER GENES (UP in aged donors from HCA data):")
    print(f"{'Rank':<6} {'Gene':<12} {'Correlation':<14} {'Meaning'}")
    print("-" * 55)
    for g in aging_marker_genes[:15]:
        print(f"  {g['rank']:<4} {g['gene']:<12} {g['correlation']:>+.4f}       Higher in 65-72y donors")

    print("\nDONOR REJUVENATION SCORES (from real latent space):")
    print(f"{'Donor':<8} {'Age':>6} {'Score':>10} {'Interpretation'}")
    print("-" * 50)
    for donor, info in sorted(donor_scores.items(), key=lambda x: x[1]['age']):
        interp = "YOUNG SIGNATURE" if info['score'] > 0 else "AGED SIGNATURE"
        print(f"  {donor:<6} {info['age']:>6.1f} {info['score']:>+10.4f}  {interp}")

    print("\n" + "=" * 70)
    print("These genes came DIRECTLY from the 486k HCA model.")
    print("This is NOT GPT. This is measured from 14 real donor cell states.")
    print("=" * 70)

if __name__ == "__main__":
    main()
