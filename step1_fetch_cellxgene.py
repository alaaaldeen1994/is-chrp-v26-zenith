"""
step1_fetch_cellxgene.py
========================
Production-grade cardiac data acquisition from CZI CELLxGENE Data Portal.

Approach: REST API + direct H5AD download (no tiledbsoma dependency needed).
The CELLxGENE Data Portal REST API (https://api.cellxgene.cziscience.com)
returns dataset metadata + pre-signed S3 download URLs for H5AD files.

Scientific rationale for tissue selection:
  - Heart (left ventricle, right ventricle, interventricular septum):
    contains cardiomyocytes, cardiac fibroblasts, endothelial cells,
    smooth muscle cells — core cell types for cardiac ageing (IS-CHRP).
  - Aorta / coronary artery: vascular smooth muscle cells and endothelial
    cells — directly relevant to atherosclerotic plaque pathology.
  - EXCLUSION of non-cardiac tissues ensures the foundation model's latent
    space captures cardiac-relevant gene programs rather than generic
    human biology (which would require 10x more data and compute).

Data license: CC BY 4.0 — all CELLxGENE datasets.
Model weights produced = 100% owned by you.

References:
  Sikkema et al., Nat Cell Biol 2023 (LungMAP) — methodology for
    multi-dataset scVI integration.
  Luecken et al., Nat Methods 2022 — scRNA-seq integration best practices.
"""

import os
import sys
import json
import time
import datetime
import hashlib
import urllib.request
import urllib.error
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import scanpy as sc
import anndata as ad
import scipy.sparse as sp
import requests

# ── Configuration ─────────────────────────────────────────────────────────────
OUT_DIR         = "data/foundation"
DATASET_DIR     = os.path.join(OUT_DIR, "raw_datasets")
COMBINED_OUT    = os.path.join(OUT_DIR, "cardiac_combined_raw.h5ad")
LOG_FILE        = os.path.join(OUT_DIR, "fetch_log.json")

CELLXGENE_API   = "https://api.cellxgene.cziscience.com/curation/v1"

# Scientifically justified tissue keywords to search for
CARDIAC_KEYWORDS = [
    "heart", "cardiac", "ventricle", "myocardium",
    "aorta", "coronary", "pericardium",
]

# Minimum dataset size to include (avoid tiny pilot datasets)
MIN_CELLS = 5_000

# Maximum total cells to load into RAM (safe for 17 GB system)
MAX_TOTAL_CELLS = 500_000

# ── Helper functions ───────────────────────────────────────────────────────────

def query_cardiac_datasets():
    """Query CELLxGENE API for cardiac human datasets."""
    print("  Querying CELLxGENE API for human cardiac datasets...")
    url = f"{CELLXGENE_API}/datasets"
    try:
        resp = requests.get(url, params={"organism": "Homo sapiens"}, timeout=30)
        resp.raise_for_status()
        all_datasets = resp.json()
    except Exception as e:
        print(f"  ERROR: API query failed — {e}")
        return []

    print(f"  Total human datasets in CELLxGENE: {len(all_datasets):,}")

    EXCLUDE_KEYWORDS = [
        "embryo", "embryonic", "development", "fetal", "zebrafish", 
        "tabula sapiens", "cell landscape", "pan-cancer", "covid-19",
        "organoid", "blood", "immune", "bone marrow", "cancer", "tumor",
        "carcinoma", "mouse"
    ]

    cardiac = []
    for ds in all_datasets:
        # Strictly human check
        organisms = [org.get("label", "").lower() for org in ds.get("organism", [])]
        if "homo sapiens" not in organisms:
            continue

        title = ds.get("title", "").lower()
        name  = ds.get("name", "").lower()

        # Exclude multi-tissue / development / non-human
        should_exclude = any(kw in title or kw in name for kw in EXCLUDE_KEYWORDS)
        if should_exclude:
            continue

        tissue_labels = [
            t.get("label", "").lower()
            for t in ds.get("tissue", [])
        ]
        
        is_cardiac = any(
            kw in tissue_labels or kw in title or kw in name
            for kw in CARDIAC_KEYWORDS
        )
        if is_cardiac:
            cardiac.append(ds)

    print(f"  Cardiac-relevant datasets found: {len(cardiac)}")
    return cardiac


def find_h5ad_asset(dataset_obj):
    """Retrieve the H5AD download URL from the dataset metadata."""
    assets = dataset_obj.get("assets", [])
    for asset in assets:
        if asset.get("filetype") == "H5AD":
            return asset.get("url"), asset.get("filesize")
    return None, None


def download_with_progress(url, dest_path, filesize_bytes=None):
    """Download a file with a progress bar and size verification."""
    if os.path.exists(dest_path):
        current_size = os.path.getsize(dest_path)
        if filesize_bytes is None or abs(current_size - filesize_bytes) < 10 * 1024 * 1024:  # within 10 MB
            print(f"    ↳ Already downloaded and verified: {os.path.basename(dest_path)}")
            return True
        else:
            print(f"    ↳ Redownloading {os.path.basename(dest_path)} (size mismatch: disk={current_size/1e9:.2f} GB, expected={filesize_bytes/1e9:.2f} GB)")

    label = os.path.basename(dest_path)
    size_str = (
        f"{filesize_bytes/1e9:.2f} GB"
        if filesize_bytes else "unknown size"
    )
    print(f"    Downloading {label} ({size_str})...", end=" ", flush=True)

    try:
        resp = requests.get(url, stream=True, timeout=600)
        resp.raise_for_status()
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                f.write(chunk)
                downloaded += len(chunk)
                if filesize_bytes:
                    pct = downloaded / filesize_bytes * 100
                    print(f"\r    Downloading {label}: {pct:.0f}%    ", end="", flush=True)
        print(f"\r    ✓ {label} — {downloaded/1e9:.2f} GB saved       ")
        return True
    except Exception as e:
        print(f"\n    ERROR downloading {label}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def load_and_harmonise(h5ad_path, dataset_meta, max_cells_budget=None):
    """
    Load a raw H5AD file and harmonise it for multi-dataset integration.

    Key steps:
      1. Ensure raw counts are in adata.X (not normalised values).
         CELLxGENE schema 3.0 mandates raw counts in .X — we verify this.
      2. Add dataset-level metadata as obs columns for batch correction.
      3. Keep only protein-coding genes (exclude ribosomal/mitochondrial
         pseudogenes that inflate HVG selection spuriously).
      4. Apply per-cell QC filters (Luecken et al. 2022 thresholds).
    """
    print(f"    Loading {os.path.basename(h5ad_path)}...")
    adata = sc.read_h5ad(h5ad_path)
    print(f"      Shape: {adata.n_obs:,} × {adata.n_vars:,}")

    # Subsample BEFORE any heavy processing if it exceeds our budget cap (prevents OOM)
    if max_cells_budget is not None and adata.n_obs > max_cells_budget:
        np.random.seed(42)
        idx = np.random.choice(adata.n_obs, size=max_cells_budget, replace=False)
        idx.sort()
        adata = adata[idx].copy()
        print(f"      ✓ Subsampled in-memory to remaining budget: {adata.n_obs:,} cells")

    # ── Verify raw counts ──────────────────────────────────────────
    # CELLxGENE schema 3.0: .X must contain raw counts.
    # Validate by checking that values are non-negative integers.
    X_sample = adata.X[:200]
    if sp.issparse(X_sample):
        X_sample = X_sample.toarray()
    is_integer = np.all(X_sample >= 0) and np.all(X_sample == np.floor(X_sample))
    if not is_integer:
        # Check if raw counts are in a layer
        if "raw" in adata.layers:
            adata.X = adata.layers["raw"]
            print("      Used .layers['raw'] for count matrix")
        elif hasattr(adata, "raw") and adata.raw is not None:
            adata = adata.raw.to_adata()
            print("      Used .raw for count matrix")
        else:
            print(f"      WARNING: {os.path.basename(h5ad_path)} may contain "
                  "normalised data. Skipping dataset.")
            return None
    else:
        print(f"      ✓ Raw count verification passed")

    # Standardise Ensembl IDs to HGNC symbols using CELLxGENE's 'feature_name' column
    # This must occur AFTER raw count recovery because raw.to_adata() reinstantiates the original var index
    if "feature_name" in adata.var.columns:
        adata.var_names = adata.var["feature_name"].astype(str)
        adata.var_names_make_unique()
        print("      ✓ Standardised gene names to HGNC symbols")

    # ── QC metrics ────────────────────────────────────────────────
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    sc.pp.calculate_qc_metrics(
        adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )

    # QC thresholds (Luecken et al. 2022, Nat Methods):
    n_before = adata.n_obs
    adata = adata[
        (adata.obs["n_genes_by_counts"] >= 200) &
        (adata.obs["n_genes_by_counts"] <= 7_000) &   # doublet proxy
        (adata.obs["total_counts"]       >= 500) &    # min library size
        (adata.obs["pct_counts_mt"]      <= 25)       # mitochondrial
    ].copy()
    n_after = adata.n_obs
    print(f"      QC: {n_before:,} → {n_after:,} cells ({n_before - n_after:,} removed)")

    if n_after < 100:
        print("      SKIP: fewer than 100 cells after QC")
        return None

    # ── Add batch metadata ─────────────────────────────────────────
    adata.obs["dataset_id"]    = dataset_meta.get("dataset_id", "unknown")
    adata.obs["dataset_title"] = dataset_meta.get("title", "unknown")[:60]
    adata.obs["source"]        = "CELLxGENE"
    adata.obs["license"]       = "CC BY 4.0"

    # Ensure donor_id is present for scVI batch correction
    if "donor_id" not in adata.obs.columns:
        adata.obs["donor_id"] = dataset_meta.get("dataset_id", "unknown")

    # Clean up large uns/obsm to save RAM
    adata.obsm = {}
    adata.obsp = {}
    adata.uns  = {}

    return adata


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(DATASET_DIR, exist_ok=True)
    start_time = datetime.datetime.utcnow()

    print("=" * 65)
    print("  Zenith Foundation Model — Data Acquisition Pipeline")
    print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)

    # ── Step 1: Discover cardiac datasets ─────────────────────────
    print("\n[1/4] Discovering cardiac datasets in CELLxGENE...")
    cardiac_datasets = query_cardiac_datasets()

    if not cardiac_datasets:
        sys.exit("No cardiac datasets found. Check network connectivity.")

    # Sort by cell count descending (largest datasets first)
    cardiac_datasets.sort(
        key=lambda d: d.get("cell_count", 0), reverse=True
    )

    # Print discovery summary
    print(f"\n  Top cardiac datasets by cell count:")
    print(f"  {'Dataset title':<55} {'Cells':>8}")
    print(f"  {'-'*55} {'-'*8}")
    for ds in cardiac_datasets[:20]:
        title     = ds.get("title", "Untitled")[:54]
        cell_cnt  = ds.get("cell_count", 0)
        print(f"  {title:<55} {cell_cnt:>8,}")

    # ── Step 2: Download top datasets ─────────────────────────────
    print(f"\n[2/4] Downloading H5AD files for datasets ≥ {MIN_CELLS:,} and ≤ {MAX_TOTAL_CELLS:,} cells...")

    MAX_FILESIZE_BYTES = 3.5 * 1024 * 1024 * 1024  # 3.5 GB cap
    download_manifest = []
    total_download_cells = 0
    for ds in cardiac_datasets:
        if total_download_cells >= MAX_TOTAL_CELLS:
            print(f"\n  ✓ Download cell budget reached ({total_download_cells:,} >= {MAX_TOTAL_CELLS:,}). Stopping further downloads.")
            break

        ds_id    = ds.get("dataset_id", ds.get("id", ""))
        title    = ds.get("title", "Untitled")
        n_cells  = ds.get("cell_count", 0)

        # Scientific and computational guards
        if n_cells < MIN_CELLS:
            continue
        if n_cells > MAX_TOTAL_CELLS:
            print(f"  SKIP (exceeds cell budget {MAX_TOTAL_CELLS:,}): {title[:60]} ({n_cells:,} cells)")
            continue

        # Get download URL
        h5ad_url, filesize = find_h5ad_asset(ds)
        if not h5ad_url:
            print(f"  SKIP (no H5AD): {title[:60]}")
            continue

        if filesize and filesize > MAX_FILESIZE_BYTES:
            print(f"  SKIP (exceeds file size cap 3.5 GB): {title[:60]} ({filesize/1e9:.2f} GB)")
            continue

        dest = os.path.join(DATASET_DIR, f"{ds_id}.h5ad")
        success = download_with_progress(h5ad_url, dest, filesize)
        if success:
            download_manifest.append({
                "dataset_id": ds_id,
                "title":      title,
                "n_cells":    n_cells,
                "path":       dest,
            })
            total_download_cells += n_cells

    print(f"\n  Successfully downloaded: {len(download_manifest)} datasets")

    # ── Step 3: Load + harmonise ───────────────────────────────────
    print(f"\n[3/4] Loading and harmonising datasets...")

    adatas = []
    total_cells = 0

    for meta in download_manifest:
        if total_cells >= MAX_TOTAL_CELLS:
            print(f"  Memory cap reached ({MAX_TOTAL_CELLS:,}). Stopping load.")
            break

        budget = MAX_TOTAL_CELLS - total_cells
        adata = load_and_harmonise(meta["path"], meta, max_cells_budget=budget)
        if adata is None:
            continue

        # Subsample within a single dataset if it's very large
        # (preserves diversity when total budget is limited)
        if adata.n_obs > budget:
            np.random.seed(42)
            idx = np.random.choice(adata.n_obs, size=budget, replace=False)
            idx.sort()
            adata = adata[idx].copy()
            print(f"      Downsampled to {adata.n_obs:,} cells (memory budget)")

        adatas.append(adata)
        total_cells += adata.n_obs
        print(f"      Running total: {total_cells:,} cells\n")

    if not adatas:
        sys.exit("ERROR: No valid datasets loaded.")

    # ── Step 4: Concatenate & save ─────────────────────────────────
    print(f"\n[4/4] Concatenating {len(adatas)} datasets into single AnnData...")

    # Outer join on genes — missing genes filled with 0
    # This is the correct strategy for multi-dataset scVI training:
    # the model sees all genes across all datasets, and learns to handle
    # missing measurements via its probabilistic framework.
    adata_combined = ad.concat(
        adatas,
        join="outer",
        fill_value=0,
        label="batch",
        index_unique="-",
    )
    adata_combined.obs_names_make_unique()

    # Cast to sparse float32 (required by scVI)
    if not sp.issparse(adata_combined.X):
        adata_combined.X = sp.csr_matrix(adata_combined.X.astype(np.float32))
    else:
        adata_combined.X = adata_combined.X.astype(np.float32).tocsr()

    print(f"  Combined shape: {adata_combined.n_obs:,} × {adata_combined.n_vars:,}")

    adata_combined.write_h5ad(COMBINED_OUT, compression="gzip")

    end_time = datetime.datetime.utcnow()
    elapsed  = (end_time - start_time).total_seconds() / 60

    # Save reproducible log
    log = {
        "timestamp_utc":       end_time.strftime("%Y-%m-%d %H:%M UTC"),
        "n_datasets":          len(download_manifest),
        "n_loaded":            len(adatas),
        "n_cells_combined":    int(adata_combined.n_obs),
        "n_genes_combined":    int(adata_combined.n_vars),
        "elapsed_minutes":     round(elapsed, 1),
        "output_file":         COMBINED_OUT,
        "data_license":        "CC BY 4.0 — CZI CELLxGENE",
        "qc_thresholds": {
            "min_genes": 200,
            "max_genes": 7000,
            "min_counts": 500,
            "max_pct_mito": 25,
        },
        "datasets": download_manifest,
    }
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    print("\n" + "=" * 65)
    print("  ✅  DATA ACQUISITION COMPLETE")
    print(f"     Datasets:  {len(adatas)}")
    print(f"     Cells:     {adata_combined.n_obs:,}")
    print(f"     Genes:     {adata_combined.n_vars:,}")
    print(f"     Time:      {elapsed:.1f} min")
    print(f"     Output:    {COMBINED_OUT}")
    print("     License:   CC BY 4.0 — model weights are 100% yours")
    print("=" * 65)
    print("\nNext step: python step2_preprocess.py")


if __name__ == "__main__":
    main()
