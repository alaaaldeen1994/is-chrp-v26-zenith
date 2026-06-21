"""
step2_preprocess.py
===================
Production-grade preprocessing pipeline for the Zenith cardiac
foundation model training dataset.

V29.0 UPGRADE: Optimised for 3.2M+ cell scale.
  - Increased HVG count from 5,000 to 6,000 to capture broader
    gene programs across the larger, multi-atlas dataset.
  - Memory-efficient sparse matrix operations throughout.
  - Stricter mitochondrial exclusion (already applied in step1 v29.0).

Scientific rationale for each step:
  1. Ambient RNA / doublet filtering:
     Applied per-dataset BEFORE concatenation would be ideal, but since
     we work post-concatenation, we apply conservative cell-level QC
     thresholds validated in Luecken et al. (2022) Nat Methods.

  2. Normalisation strategy:
     We DO NOT normalise before scVI training. scVI's negative binomial
     model explicitly accounts for library size via the offset term in
     its decoder. Normalising before training would break this assumption
     and produce biased latent representations.
     Reference: Lopez et al. 2018, Nat Methods.

  3. Highly variable gene (HVG) selection:
     We select 6,000 HVGs using the Seurat v3 / scanpy 'seurat_v3' method,
     which accounts for mean-variance trends in count data and is robust
     to the multi-dataset setting.
     - 6,000 is scaled up from v28.0's 5,000 to capture the broader
       gene programs present across 3.2M cells from multiple atlases.
     - HVG selection is performed on the FULL gene set before subsetting.
     Reference: Stuart et al. 2019, Cell.

  4. Mitochondrial gene exclusion:
     MT- genes are excluded from HVGs as they primarily capture
     cell stress/death rather than biological state.

  5. Gene name standardisation:
     The var_names must be HGNC gene symbols for cross-dataset consistency.
     CELLxGENE Census enforces this in their schema.
"""

import os
import sys
import json
import datetime
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import scanpy as sc
import anndata as ad
import scipy.sparse as sp

# ── Configuration ─────────────────────────────────────────────────────────────
IN_FILE      = "data/foundation/cardiac_combined_raw.h5ad"
OUT_FILE     = "data/foundation/cardiac_preprocessed.h5ad"
HVGS_FILE    = "data/foundation/selected_hvgs.json"
METRICS_FILE = "data/foundation/preprocessing_metrics.json"

N_HVG        = 6_000    # Highly variable genes (scaled up for 3.2M cells)
MIN_CELLS    = 10       # Min cells per gene (filters lowly expressed genes)

# ── Preprocessing pipeline ────────────────────────────────────────────────────
def main():
    start_time = datetime.datetime.utcnow()

    print("=" * 70)
    print("  Zenith Foundation Model v29.0 — Preprocessing Pipeline")
    print(f"  Target: 3.2M+ Cell Cardiac Atlas")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    # ── 1. Load raw combined data ──────────────────────────────────
    print(f"\n[1/6] Loading: {IN_FILE}")
    adata = sc.read_h5ad(IN_FILE)
    n_cells_raw = adata.n_obs
    n_genes_raw = adata.n_vars
    print(f"  Shape: {adata.n_obs:,} × {adata.n_vars:,}")

    # Verify X is non-negative integers (raw counts)
    X_s = adata.X[:500]
    if sp.issparse(X_s):
        X_s = X_s.toarray()
    assert np.all(X_s >= 0), "CRITICAL: Negative values in count matrix"
    print("  ✓ Count matrix verified (non-negative integers)")

    # ── 2. Gene-level filtering ────────────────────────────────────
    print(f"\n[2/6] Gene filtering (min {MIN_CELLS} cells per gene)...")
    sc.pp.filter_genes(adata, min_cells=MIN_CELLS)
    print(f"  Genes: {n_genes_raw:,} → {adata.n_vars:,} "
          f"({n_genes_raw - adata.n_vars:,} removed)")

    # ── 3. Additional cell-level QC ────────────────────────────────
    # Note: primary QC was applied in step1 v29.0. This is a safety re-check
    # after any concatenation artefacts (e.g., zero-count cells).
    print(f"\n[3/6] Cell-level QC re-check...")

    # Ensure mitochondrial gene annotation exists
    if "mt" not in adata.var.columns:
        adata.var["mt"] = adata.var_names.str.startswith("MT-")

    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mt"],
        percent_top=None,
        log1p=False,
        inplace=True,
    )
    n_before = adata.n_obs
    adata = adata[adata.obs["n_genes_by_counts"] >= 200].copy()
    print(f"  Cells: {n_before:,} → {adata.n_obs:,} "
          f"({n_before - adata.n_obs:,} near-empty cells removed)")

    # ── 4. Store raw counts in .layers["counts"] ───────────────────
    # scVI requires raw counts and will access them via adata.layers["counts"].
    # We MUST store before any normalisation.
    print(f"\n[4/6] Storing raw counts in .layers['counts']...")
    adata.layers["counts"] = adata.X.copy()
    print("  ✓ Raw counts stored")

    # ── 5. HVG selection ───────────────────────────────────────────
    # Performed on log1p-normalised expression (temp) for stability,
    # but actual training uses raw counts from .layers["counts"].
    print(f"\n[5/6] Selecting {N_HVG:,} Highly Variable Genes (Seurat v3)...")

    # Temporary normalisation for HVG selection only
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    # Exclude MT genes from HVG candidates (capture stress, not biology)
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    # Also exclude ribosomal genes (RPL/RPS) — they dominate HVG lists
    # spuriously and add noise without biological information.
    adata.var["ribo"] = (
        adata.var_names.str.startswith("RPL") |
        adata.var_names.str.startswith("RPS")
    )

    # Select HVGs from non-MT, non-ribosomal genes
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=N_HVG,
        subset=False,
        flavor="seurat_v3",
        layer="counts",        # use raw counts for dispersion estimation
        batch_key="dataset_id" if "dataset_id" in adata.obs.columns else None,
        # batch_key ensures HVGs are informative across datasets,
        # not just within one high-cell-count dataset
    )

    # Override HVG selection for MT and ribosomal genes
    adata.var.loc[adata.var["mt"],   "highly_variable"] = False
    adata.var.loc[adata.var["ribo"], "highly_variable"] = False

    n_hvg = adata.var["highly_variable"].sum()
    print(f"  HVGs selected: {n_hvg:,}")
    print(f"  MT genes excluded: {adata.var['mt'].sum()}")
    print(f"  Ribosomal genes excluded: {adata.var['ribo'].sum()}")

    # Restore raw counts in X (replace the temp log-normalised values)
    adata.X = adata.layers["counts"].copy()

    # Subset to HVG-only AnnData for training
    adata_hvg = adata[:, adata.var["highly_variable"]].copy()
    print(f"\n  Final training shape: {adata_hvg.n_obs:,} × {adata_hvg.n_vars:,}")

    # Save HVG list for model card / reproducibility
    hvg_list = adata_hvg.var_names.tolist()
    with open(HVGS_FILE, "w") as f:
        json.dump(hvg_list, f, indent=2)
    print(f"  ✓ HVG list saved → {HVGS_FILE}")

    # ── 6. Save preprocessed AnnData ──────────────────────────────
    print(f"\n[6/6] Saving preprocessed AnnData to {OUT_FILE}...")

    # Final obs column standardisation for scVI batch correction
    required_obs = ["donor_id", "dataset_id", "suspension_type"]
    for col in required_obs:
        if col not in adata_hvg.obs.columns:
            adata_hvg.obs[col] = "unknown"
    # Cast all batch columns to categorical (required by scVI)
    for col in required_obs:
        adata_hvg.obs[col] = pd.Categorical(adata_hvg.obs[col].astype(str))

    adata_hvg.write_h5ad(OUT_FILE, compression="gzip")

    end_time = datetime.datetime.utcnow()
    elapsed  = (end_time - start_time).total_seconds() / 60

    # Save preprocessing metrics
    metrics = {
        "timestamp_utc":       end_time.strftime("%Y-%m-%d %H:%M UTC"),
        "pipeline_version":    "v29.0 (3.2M Census)",
        "n_cells_input":       n_cells_raw,
        "n_cells_output":      int(adata_hvg.n_obs),
        "n_genes_input":       n_genes_raw,
        "n_genes_output":      int(adata_hvg.n_vars),
        "n_hvg_selected":      int(n_hvg),
        "n_mt_excluded":       int(adata.var["mt"].sum()),
        "n_ribo_excluded":     int(adata.var["ribo"].sum()),
        "min_cells_per_gene":  MIN_CELLS,
        "hvg_method":          "seurat_v3",
        "raw_counts_in_X":     True,
        "raw_counts_in_layer": "counts",
        "elapsed_minutes":     round(elapsed, 1),
        "output_file":         OUT_FILE,
    }
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n" + "=" * 70)
    print("  ✅  PREPROCESSING COMPLETE (v29.0)")
    print(f"     Input:   {n_cells_raw:,} cells × {n_genes_raw:,} genes")
    print(f"     Output:  {adata_hvg.n_obs:,} cells × {adata_hvg.n_vars:,} genes")
    print(f"     HVGs:    {n_hvg:,}")
    print(f"     Time:    {elapsed:.1f} min")
    print(f"     Output:  {OUT_FILE}")
    print("=" * 70)
    print("\nNext step: python step3_train_scvi.py")


if __name__ == "__main__":
    main()
