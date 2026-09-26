"""
CELL-TYPE-SPECIFIC GENE EXTRACTION
===================================
Computes rejuvenation vectors and gene correlations PER CELL TYPE.
Instead of mixing all 486k cells, we split by cell type and compute:
  - Young vs Aged centroids per cell type
  - Per-cell-type gene correlations with the rejuvenation vector
  - Age delta per cell type

Source: Litvinukova et al., Nature 2020
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json, pickle
import numpy as np
import scanpy as sc
import scvi

# ── Config ────────────────────────────────────────────────
DATA_PATH = "data/hca_full/heart_adult_full.h5ad"
MODEL_DIR = "models/scvi_model_486k_real"
OUTPUT_PATH = "models/cell_type_genes.json"
CLOCK_PATH = "models/age_clock.pkl"

DONOR_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5,
    "D5": 67.5, "D6": 72.5, "D7": 62.5, "D11": 62.5,
    "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5,
    "H6": 42.5, "H7": 47.5,
}

YOUNG_MAX = 55.0
AGED_MIN = 65.0

# Focus on the major cardiac cell types (>3000 cells each)
TARGET_CELL_TYPES = [
    "regular ventricular cardiac myocyte",   # 125k
    "pericyte",                               # 78k
    "fibroblast",                             # 59k
    "capillary endothelial cell",             # 58k
    "regular atrial cardiac myocyte",         # 23k
    "endothelial cell of artery",             # 20k
    "smooth muscle cell",                     # 16k
    "macrophage",                             # 15k
    "endothelial cell",                       # 13k
    "vein endothelial cell",                  # 8k
    "neural cell",                            # 4k
    "epicardial adipocyte",                   # 4k
]


def main():
    print("=" * 65)
    print("CELL-TYPE-SPECIFIC GENE EXTRACTION")
    print("=" * 65)

    # ── Step 1: Load data ────────────────────────────────────
    print(f"\n[1/5] Loading {DATA_PATH}...")
    adata = sc.read_h5ad(DATA_PATH)
    print(f"  {adata.n_obs:,} cells, {adata.n_vars:,} genes")

    # Add donor ages
    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)
    adata.obs["age_group"] = "middle"
    adata.obs.loc[adata.obs["donor_age"] <= YOUNG_MAX, "age_group"] = "young"
    adata.obs.loc[adata.obs["donor_age"] >= AGED_MIN, "age_group"] = "aged"

    # Drop .raw
    if adata.raw is not None:
        adata.raw = None

    # ── Step 2: Load scVI model ──────────────────────────────
    print(f"\n[2/5] Loading scVI model from {MODEL_DIR}...")
    # We need to setup and load on a compatible subset
    # First, select HVGs matching what the model was trained on
    sc.pp.highly_variable_genes(adata, n_top_genes=5000, subset=True)
    print(f"  After HVG: {adata.n_vars} genes")

    scvi.model.SCVI.setup_anndata(adata)
    model = scvi.model.SCVI.load(MODEL_DIR, adata=adata)
    print("  scVI model loaded")

    # Get latent representations for ALL cells
    print("  Computing latent representations...")
    latent = model.get_latent_representation()
    print(f"  Latent shape: {latent.shape}")

    # Load age clock
    clock = None
    if os.path.exists(CLOCK_PATH):
        with open(CLOCK_PATH, "rb") as f:
            pkg = pickle.load(f)
        clock = pkg["model"]
        print(f"  Age clock loaded (MAE={pkg.get('cv_mae_years', '?'):.1f}y)")

    # ── Step 3: Per-cell-type analysis ───────────────────────
    print(f"\n[3/5] Computing per-cell-type rejuvenation vectors...")
    cell_type_results = {}

    for ct in TARGET_CELL_TYPES:
        mask = (adata.obs["cell_type"] == ct).values
        n_cells = mask.sum()

        if n_cells < 100:
            print(f"  SKIP {ct} ({n_cells} cells — too few)")
            continue

        ct_latent = latent[mask]
        ct_ages = adata.obs.loc[mask, "age_group"].values
        ct_donor_ages = adata.obs.loc[mask, "donor_age"].values

        young_mask = ct_ages == "young"
        aged_mask = ct_ages == "aged"

        n_young = young_mask.sum()
        n_aged = aged_mask.sum()

        if n_young < 20 or n_aged < 20:
            print(f"  SKIP {ct} ({n_cells:,} cells, but young={n_young}, aged={n_aged} — insufficient)")
            continue

        # Compute centroids
        young_centroid = ct_latent[young_mask].mean(axis=0)
        aged_centroid = ct_latent[aged_mask].mean(axis=0)
        rejuv_vector = young_centroid - aged_centroid
        magnitude = float(np.linalg.norm(rejuv_vector))

        # Age delta from clock
        age_delta = None
        if clock is not None:
            try:
                pred_young = float(clock.predict(young_centroid.reshape(1, -1))[0])
                pred_aged = float(clock.predict(aged_centroid.reshape(1, -1))[0])
                age_delta = round(pred_aged - pred_young, 1)
            except:
                pass

        # ── Step 4: Gene correlations for this cell type ─────
        # Correlate each gene's expression with projection onto rejuv vector
        projections = ct_latent @ rejuv_vector  # scalar per cell

        # Get gene expression matrix for this cell type
        ct_X = adata.X[mask]
        n_genes_total = ct_X.shape[1]
        gene_names = adata.var_names.tolist()

        # Center projections and get std
        y = projections - projections.mean()
        y_std = y.std()
        if y_std < 1e-10:
            print(f"  SKIP {ct} — zero variance in projections")
            continue

        # Compute Pearson correlation using highly optimized chunked matrix math
        # to avoid both python loop overhead and high memory peaks.
        correlations = []
        chunk_size = 1000
        for start_g in range(0, n_genes_total, chunk_size):
            end_g = min(start_g + chunk_size, n_genes_total)
            chunk_dense = ct_X[:, start_g:end_g]
            if hasattr(chunk_dense, 'toarray'):
                chunk_dense = chunk_dense.toarray()
            elif not isinstance(chunk_dense, np.ndarray):
                chunk_dense = np.asarray(chunk_dense)

            # Compute column means, stds, and covariance with centered projections
            X_std = chunk_dense.std(axis=0)
            cov = (chunk_dense.T @ y) / len(y)

            with np.errstate(divide='ignore', invalid='ignore'):
                r_chunk = cov / (X_std * y_std)

            for local_idx, g_idx in enumerate(range(start_g, end_g)):
                r = float(r_chunk[local_idx])
                if np.isfinite(r) and X_std[local_idx] >= 1e-10:
                    correlations.append((gene_names[g_idx], r))

        # Sort by correlation
        correlations.sort(key=lambda x: x[1], reverse=True)

        # Top 50 pro-rejuvenation (highest positive r = up in young)
        pro_genes = [
            {"gene": g, "correlation": round(r, 4), "rank": i+1}
            for i, (g, r) in enumerate(correlations[:50])
        ]

        # Top 50 aging markers (most negative r = up in aged)
        aging_genes = [
            {"gene": g, "correlation": round(r, 4), "rank": i+1}
            for i, (g, r) in enumerate(correlations[-50:][::-1])
        ]

        # Create a clean key name
        ct_key = ct.replace(",", "").replace("-", "_").replace(" ", "_").lower()

        cell_type_results[ct_key] = {
            "cell_type": ct,
            "n_cells": int(n_cells),
            "n_young": int(n_young),
            "n_aged": int(n_aged),
            "rejuv_vector_magnitude": round(magnitude, 4),
            "age_delta": age_delta,
            "n_genes_correlated": len(correlations),
            "pro_rejuvenation_genes": pro_genes,
            "aging_marker_genes": aging_genes,
        }

        print(f"  OK  {ct}: {n_cells:,} cells (young={n_young:,}, aged={n_aged:,}), "
              f"mag={magnitude:.3f}, delta={age_delta}y, "
              f"top_pro={pro_genes[0]['gene']} (r={pro_genes[0]['correlation']:.3f})")

    # ── Step 5: Save ─────────────────────────────────────────
    print(f"\n[5/5] Saving to {OUTPUT_PATH}...")
    output = {
        "source": "Litvinukova et al., Nature 2020",
        "doi": "10.1038/s41586-020-2797-4",
        "total_cells": int(adata.n_obs),
        "total_genes": int(adata.n_vars),
        "n_cell_types": len(cell_type_results),
        "young_age_range": f"<={YOUNG_MAX}y",
        "aged_age_range": f">={AGED_MIN}y",
        "method": "Per-cell-type Pearson correlation with cell-type-specific rejuvenation vector",
        "cell_types": cell_type_results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 65}")
    print(f"COMPLETE: {len(cell_type_results)} cell types analysed")
    for k, v in cell_type_results.items():
        print(f"  {v['cell_type']}: {v['n_cells']:,} cells, "
              f"delta={v['age_delta']}y, "
              f"top={v['pro_rejuvenation_genes'][0]['gene']}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
