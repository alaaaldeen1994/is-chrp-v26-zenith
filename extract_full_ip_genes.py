"""
FULL IP GENE DISCOVERY — All 32,383 HCA Genes
===============================================
Runs on all genes in the dataset (not just the 5,000 HVGs).
Uses the existing trained latent rejuvenation vector — NO RETRAINING.

Method:
  1. Load trained scVI model
  2. Load ALL 32,383 genes from heart_adult_full.h5ad
  3. Project each gene's expression onto the rejuvenation vector
  4. Rank all 32,383 by correlation with youth direction

Device: Surface Pro 7+, 16GB RAM — feasible.
Saves: models/real_ip_genes_full.json
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json
import numpy as np
import scanpy as sc
import scvi
import scipy.sparse as sp

DONOR_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5,
    "D5": 67.5, "D6": 72.5, "D7": 62.5, "D11": 62.5,
    "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5,
    "H6": 42.5, "H7": 47.5,
}
YOUNG_DONORS = [d for d, age in DONOR_AGE_MAP.items() if age <= 55]
AGED_DONORS  = [d for d, age in DONOR_AGE_MAP.items() if age >= 65]

MODEL_DIR      = "models/scvi_model_486k_real"
CENTROIDS_PATH = "models/real_centroids.json"
DATA_PATH      = "data/hca_full/heart_adult_full.h5ad"
OUT_PATH       = "models/real_ip_genes_full.json"

def main():
    print("=" * 70)
    print("FULL IP GENE DISCOVERY — All 32,383 HCA Genes")
    print("Device: Surface Pro 7+, 16GB RAM")
    print("Source: Litvinukova et al., Nature 2020")
    print("=" * 70)

    # ── 1. Load rejuvenation vector from saved centroids ─────────────────
    print(f"\n[1/5] Loading rejuvenation vector from centroids...")
    with open(CENTROIDS_PATH) as f:
        centroids = json.load(f)
    young_vec = np.array(centroids["young"]["centroid"])
    aged_vec  = np.array(centroids["aged"]["centroid"])
    rejuv_vec = young_vec - aged_vec
    rejuv_unit = rejuv_vec / (np.linalg.norm(rejuv_vec) + 1e-10)
    print(f"  Rejuvenation vector magnitude: {np.linalg.norm(rejuv_vec):.4f}")

    # ── 2. Load scVI model ────────────────────────────────────────────────
    print(f"\n[2/5] Loading trained scVI model...")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = scvi.model.SCVI.load(MODEL_DIR)
    print("  Model loaded.")

    # ── 3. Load ALL cells with ALL genes (no HVG filter) ─────────────────
    print(f"\n[3/5] Loading ALL 32,383 genes from HCA data...")
    adata_full = sc.read_h5ad(DATA_PATH)
    adata_full.raw = None
    adata_full.obs["donor_age"] = adata_full.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)
    total_genes = adata_full.n_vars
    print(f"  Full dataset: {adata_full.n_obs:,} cells × {total_genes:,} genes")

    # Use same stratified subsample for latent embedding (5k HVG subset)
    np.random.seed(42)
    donor_counts = adata_full.obs['donor_id'].value_counts()
    total = donor_counts.sum()
    SUBSAMPLE_N = 100_000
    indices = []
    for donor, count in donor_counts.items():
        n_sample = max(1, int(SUBSAMPLE_N * count / total))
        donor_idx = np.where(adata_full.obs['donor_id'] == donor)[0]
        chosen = np.random.choice(donor_idx, size=min(n_sample, len(donor_idx)), replace=False)
        indices.extend(chosen.tolist())
    indices = sorted(indices)
    adata_sub_full = adata_full[indices].copy()
    print(f"  Subsampled: {adata_sub_full.n_obs:,} cells × {total_genes:,} genes")

    # ── 4. Get latent embeddings using the 5k HVG model ──────────────────
    print(f"\n[4/5] Computing latent embeddings via scVI model...")
    # The model was trained on 5k HVGs — setup that subset for embedding
    adata_hvg = adata_sub_full.copy()
    sc.pp.highly_variable_genes(adata_hvg, n_top_genes=5000, subset=True)
    scvi.model.SCVI.setup_anndata(adata_hvg)
    model.adata = adata_hvg

    latent = model.get_latent_representation()  # (n_cells, 20)
    print(f"  Latent embeddings: {latent.shape}")

    # Project cells onto rejuvenation axis
    cell_scores = latent @ rejuv_unit  # (n_cells,)
    cell_scores_norm = (cell_scores - cell_scores.mean()) / (cell_scores.std() + 1e-10)

    # ── 5. Correlate ALL 32,383 genes with rejuvenation scores ───────────
    print(f"\n[5/5] Correlating ALL {total_genes:,} genes with rejuvenation vector...")
    print("  This will take ~5-10 minutes on 16GB RAM...")

    # Get full gene expression for the subsampled cells
    # Do NOT convert the full matrix to dense — use sparse directly
    X_full = adata_sub_full.X  # keep sparse
    if not sp.issparse(X_full):
        X_full = sp.csr_matrix(X_full)
    else:
        X_full = X_full.tocsc()  # column-efficient for gene batches

    gene_names = adata_sub_full.var["feature_name"].tolist()
    gene_ids   = adata_sub_full.var.index.tolist()

    n_genes = X_full.shape[1]
    gene_correlations = np.zeros(n_genes, dtype=np.float32)

    # Batch compute from sparse — never materialise the full dense matrix
    BATCH = 500
    import time as _time
    t0 = _time.time()
    for start in range(0, n_genes, BATCH):
        end = min(start + BATCH, n_genes)
        if sp.issparse(X_full):
            batch = np.array(X_full[:, start:end].todense(), dtype=np.float64)
        else:
            batch = X_full[:, start:end].astype(np.float64)
        means = batch.mean(axis=0)
        stds  = batch.std(axis=0) + 1e-10
        batch_norm = (batch - means) / stds
        corrs = (cell_scores_norm @ batch_norm) / len(cell_scores_norm)
        gene_correlations[start:end] = corrs.astype(np.float32)

        if (start // BATCH) % 5 == 0:
            elapsed = _time.time() - t0
            pct = 100 * end / n_genes
            rate = end / max(elapsed, 1)
            eta  = (n_genes - end) / max(rate, 1)
            print(f"  {end:>6,}/{n_genes:,} genes ({pct:.0f}%) | "
                  f"{elapsed/60:.1f} min elapsed | ETA {eta/60:.1f} min")

    print(f"  Done. {n_genes:,} genes correlated.")

    # ── Rank and save ─────────────────────────────────────────────────────
    sorted_pro  = np.argsort(gene_correlations)[::-1]   # highest = most pro-youth
    sorted_aged = np.argsort(gene_correlations)          # lowest = most pro-aging

    pro_list = [
        {
            "rank": int(r) + 1,
            "gene": gene_names[i],
            "ensembl_id": gene_ids[i],
            "correlation": round(float(gene_correlations[i]), 4)
        }
        for r, i in enumerate(sorted_pro[:200])  # save top 200
    ]
    aging_list = [
        {
            "rank": int(r) + 1,
            "gene": gene_names[i],
            "ensembl_id": gene_ids[i],
            "correlation": round(float(gene_correlations[i]), 4)
        }
        for r, i in enumerate(sorted_aged[:200])  # save top 200
    ]

    result = {
        "source": "Litvinukova et al., Nature 2020",
        "doi": "10.1038/s41586-020-2797-4",
        "model": MODEL_DIR,
        "method": "Pearson correlation with latent rejuvenation vector (full gene set)",
        "n_cells": int(adata_sub_full.n_obs),
        "n_genes_total_in_hca": int(total_genes),
        "n_genes_analysed": int(n_genes),
        "rejuvenation_vector_magnitude": float(np.linalg.norm(rejuv_vec)),
        "pro_rejuvenation_genes": pro_list,
        "aging_marker_genes": aging_list
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # ── Print top 30 results ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"FULL IP DISCOVERY — {n_genes:,} genes analysed")
    print("=" * 70)
    print("\nTOP 30 PRO-REJUVENATION GENES (higher in 40-55y donors):")
    print(f"  {'Rank':<5} {'Gene':<20} {'Correlation'}")
    print("  " + "-" * 40)
    for g in pro_list[:30]:
        print(f"  #{g['rank']:<4} {g['gene']:<20} {g['correlation']:+.4f}")

    print("\nTOP 30 AGING MARKERS (higher in 65-72y donors):")
    print(f"  {'Rank':<5} {'Gene':<20} {'Correlation'}")
    print("  " + "-" * 40)
    for g in aging_list[:30]:
        print(f"  #{g['rank']:<4} {g['gene']:<20} {g['correlation']:+.4f}")

    print(f"\n  Saved top 200 of each to: {OUT_PATH}")
    print("=" * 70)

if __name__ == "__main__":
    main()
