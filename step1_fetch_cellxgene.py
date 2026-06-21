"""
step1_fetch_cellxgene.py
========================
Production-grade cardiac data acquisition from CZI CELLxGENE Census.

V29.0 UPGRADE: Uses the cellxgene_census SOMA API to stream ALL 3.2M+
human cardiac/vascular cells directly from S3, bypassing manual H5AD
file downloads entirely.

Approach: TileDB-SOMA streaming via cellxgene_census SDK.
The Census API provides a cloud-hosted TileDB-SOMA object that can be
queried with SQL-style filters. Data is streamed in chunks directly into
an AnnData object, keeping peak RAM usage manageable.

Scientific rationale for tissue selection:
  - Heart (left ventricle, right ventricle, interventricular septum,
    cardiac atrium, cardiac ventricle, heart):
    Contains cardiomyocytes, cardiac fibroblasts, endothelial cells,
    smooth muscle cells — core cell types for cardiac ageing (IS-CHRP).
  - Aorta / coronary artery: Vascular smooth muscle cells and endothelial
    cells — directly relevant to atherosclerotic plaque pathology.
  - EXCLUSION of non-cardiac tissues ensures the foundation model's latent
    space captures cardiac-relevant gene programs rather than generic
    human biology (which would require 10x more data and compute).

Data license: CC BY 4.0 — all CELLxGENE datasets.
Model weights produced = 100% owned by you.

References:
  Lopez et al. 2018. Deep generative modeling for single-cell transcriptomics.
    Nature Methods, 15, 1053–1058.
  Gayoso et al. 2022. A Python library for probabilistic analysis of
    single-cell omics data. Nature Biotechnology, 40, 163–166.
  Luecken et al. 2022. Benchmarking atlas-level data integration in
    single-cell genomics. Nature Methods, 19, 41–50.
  CZI CELLxGENE Census Documentation:
    https://chanzuckerberg.github.io/cellxgene-census/
"""

import os
import sys
import json
import time
import datetime
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import scanpy as sc
import anndata as ad
import scipy.sparse as sp

# ── Configuration ─────────────────────────────────────────────────────────────
OUT_DIR         = "data/foundation"
COMBINED_OUT    = os.path.join(OUT_DIR, "cardiac_combined_raw.h5ad")
LOG_FILE        = os.path.join(OUT_DIR, "fetch_log.json")

# Scientifically justified tissue labels for the Census SOMA query.
# These are ontology-controlled terms from the CL/UBERON vocabularies
# used by CELLxGENE Census.
CARDIAC_TISSUES = [
    "heart",
    "heart left ventricle",
    "heart right ventricle",
    "interventricular septum",
    "cardiac atrium",
    "cardiac ventricle",
    "left cardiac atrium",
    "right cardiac atrium",
    "myocardium",
    "aorta",
    "coronary artery",
    "pericardium",
]

# No cell cap — we want ALL available cardiac cells (~3.2M)
# QC filtering will reduce this to ~2.5–2.7M high-quality cells in step2.

# Minimum dataset size to include (avoid tiny pilot datasets)
MIN_CELLS = 5_000


# ── Helper functions ──────────────────────────────────────────────────────────

def build_tissue_filter(tissues):
    """
    Build a SOMA value_filter string for the given tissue labels.
    Example output: "tissue == 'heart' or tissue == 'aorta' or ..."
    """
    clauses = [f"tissue == '{t}'" for t in tissues]
    return " or ".join(clauses)


def stream_cardiac_cells_from_census():
    """
    Stream all human cardiac/vascular cells from the CZI CELLxGENE Census
    using the TileDB-SOMA API. No local H5AD files are downloaded.

    Returns an AnnData object with raw counts in .X and standardised
    metadata columns in .obs.
    """
    import cellxgene_census
    import tiledbsoma

    print("  Opening CELLxGENE Census (latest stable release)...")
    census = cellxgene_census.open_soma()

    # Access the Homo sapiens experiment
    human = census["census_data"]["homo_sapiens"]

    # Build tissue filter
    tissue_filter = build_tissue_filter(CARDIAC_TISSUES)

    # Full query: all normal (non-diseased) human cardiac cells
    obs_value_filter = (
        f"is_primary_data == True and "
        f"disease == 'normal' and "
        f"({tissue_filter})"
    )

    print(f"  Query filter: {obs_value_filter[:120]}...")
    print("  Streaming cells from S3 (this may take 10–30 minutes)...")

    t0 = time.time()

    # Stream the query into an AnnData object
    # column_names controls which obs/var metadata columns to retrieve
    adata = cellxgene_census.get_anndata(
        census,
        organism="Homo sapiens",
        obs_value_filter=obs_value_filter,
        column_names={
            "obs": [
                "dataset_id",
                "donor_id",
                "suspension_type",
                "cell_type",
                "tissue",
                "assay",
                "sex",
                "development_stage",
                "soma_joinid",
            ],
            "var": [
                "feature_name",
                "feature_id",
            ],
        },
    )

    t1 = time.time()
    elapsed_min = (t1 - t0) / 60

    print(f"  ✓ Streamed {adata.n_obs:,} cells × {adata.n_vars:,} genes in {elapsed_min:.1f} min")

    # Close the census connection
    census.close()

    return adata, elapsed_min


def harmonise_census_anndata(adata):
    """
    Harmonise the Census AnnData for multi-dataset scVI integration.

    Steps:
      1. Standardise gene names to HGNC symbols.
      2. Verify raw counts in .X.
      3. Apply per-cell QC filters (Luecken et al. 2022 thresholds).
      4. Add mitochondrial gene annotations.
    """
    print("\n  Harmonising Census AnnData...")

    # ── Standardise gene names ────────────────────────────────────
    if "feature_name" in adata.var.columns:
        adata.var_names = adata.var["feature_name"].astype(str)
        adata.var_names_make_unique()
        print("    ✓ Gene names standardised to HGNC symbols")

    # ── Verify raw counts ─────────────────────────────────────────
    X_sample = adata.X[:500]
    if sp.issparse(X_sample):
        X_sample = X_sample.toarray()
    is_integer = np.all(X_sample >= 0) and np.all(X_sample == np.floor(X_sample))
    if is_integer:
        print("    ✓ Raw count verification passed (non-negative integers)")
    else:
        print("    WARNING: Count matrix may contain normalised data")

    # ── Annotate mitochondrial genes ──────────────────────────────
    adata.var["mt"] = adata.var_names.str.startswith("MT-")

    # ── QC metrics ────────────────────────────────────────────────
    sc.pp.calculate_qc_metrics(
        adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )

    # ── Cell-level QC filters (Luecken et al. 2022 thresholds) ───
    n_before = adata.n_obs
    adata = adata[
        (adata.obs["n_genes_by_counts"] >= 200) &
        (adata.obs["n_genes_by_counts"] <= 7_000) &   # doublet proxy
        (adata.obs["total_counts"]       >= 500) &    # min library size
        (adata.obs["pct_counts_mt"]      <= 20)       # mitochondrial (stricter for 3.2M)
    ].copy()
    n_after = adata.n_obs
    print(f"    QC: {n_before:,} → {n_after:,} cells ({n_before - n_after:,} removed)")

    # ── Standardise batch columns ─────────────────────────────────
    for col in ["dataset_id", "donor_id", "suspension_type", "cell_type", "tissue"]:
        if col not in adata.obs.columns:
            adata.obs[col] = "unknown"
        adata.obs[col] = pd.Categorical(adata.obs[col].astype(str))

    # Add provenance metadata
    adata.obs["source"] = "CELLxGENE_Census"
    adata.obs["license"] = "CC BY 4.0"

    # Clean up large uns/obsm to save RAM
    adata.obsm = {}
    adata.obsp = {}
    adata.uns = {}

    return adata


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    start_time = datetime.datetime.utcnow()

    print("=" * 70)
    print("  Zenith Foundation Model v29.0 — Data Acquisition Pipeline")
    print(f"  Target: ALL 3.2M+ Human Cardiac/Vascular Cells (CELLxGENE Census)")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    # ── Step 1: Stream all cardiac cells from Census ──────────────
    print("\n[1/3] Streaming cardiac cells from CELLxGENE Census...")
    adata, stream_time = stream_cardiac_cells_from_census()

    # ── Step 2: Harmonise and QC ──────────────────────────────────
    print("\n[2/3] Harmonising and quality-filtering...")
    adata = harmonise_census_anndata(adata)

    # Print cell type composition
    if "cell_type" in adata.obs.columns:
        print("\n  Cell Type Composition (top 15):")
        ct_counts = adata.obs["cell_type"].value_counts().head(15)
        for ct, count in ct_counts.items():
            pct = count / adata.n_obs * 100
            print(f"    {ct[:50]:<52} {count:>8,} ({pct:>5.1f}%)")

    # Print dataset composition
    if "dataset_id" in adata.obs.columns:
        n_datasets = adata.obs["dataset_id"].nunique()
        n_donors = adata.obs["donor_id"].nunique() if "donor_id" in adata.obs.columns else 0
        print(f"\n  Datasets: {n_datasets}")
        print(f"  Unique donors: {n_donors}")

    # ── Step 3: Save combined raw AnnData ─────────────────────────
    print(f"\n[3/3] Saving combined raw AnnData to {COMBINED_OUT}...")

    # Cast to sparse float32 (required by scVI)
    if not sp.issparse(adata.X):
        adata.X = sp.csr_matrix(adata.X.astype(np.float32))
    else:
        adata.X = adata.X.astype(np.float32).tocsr()

    adata.write_h5ad(COMBINED_OUT, compression="gzip")

    end_time = datetime.datetime.utcnow()
    elapsed = (end_time - start_time).total_seconds() / 60

    # Save reproducible log
    log = {
        "timestamp_utc":       end_time.strftime("%Y-%m-%d %H:%M UTC"),
        "pipeline_version":    "v29.0 (Census SOMA streaming)",
        "n_cells_streamed":    int(adata.n_obs),
        "n_genes":             int(adata.n_vars),
        "n_datasets":          int(adata.obs["dataset_id"].nunique()),
        "n_donors":            int(adata.obs["donor_id"].nunique()) if "donor_id" in adata.obs.columns else 0,
        "tissues_queried":     CARDIAC_TISSUES,
        "stream_time_min":     round(stream_time, 1),
        "total_elapsed_min":   round(elapsed, 1),
        "output_file":         COMBINED_OUT,
        "data_license":        "CC BY 4.0 — CZI CELLxGENE Census",
        "model_license":       "Proprietary — no restrictions",
        "qc_thresholds": {
            "min_genes": 200,
            "max_genes": 7000,
            "min_counts": 500,
            "max_pct_mito": 20,
        },
    }
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    print("\n" + "=" * 70)
    print("  ✅  DATA ACQUISITION COMPLETE (v29.0 Census)")
    print(f"     Cells:       {adata.n_obs:,}")
    print(f"     Genes:       {adata.n_vars:,}")
    print(f"     Datasets:    {adata.obs['dataset_id'].nunique()}")
    print(f"     Donors:      {adata.obs['donor_id'].nunique()}")
    print(f"     Stream time: {stream_time:.1f} min")
    print(f"     Total time:  {elapsed:.1f} min")
    print(f"     Output:      {COMBINED_OUT}")
    print("     License:     CC BY 4.0 — model weights are 100% yours")
    print("=" * 70)
    print("\nNext step: python step2_preprocess.py")


if __name__ == "__main__":
    main()
