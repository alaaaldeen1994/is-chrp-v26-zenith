import os
import re
import sys
import json
import glob
import datetime
import h5py
import torch
import numpy as np
import pandas as pd
import scipy.stats as stats

sys.stdout.reconfigure(encoding="utf-8")

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_DIR)

def main():
    print("=" * 80)
    print("PHASE A READ-ONLY VERIFICATION AUDIT")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # A.1: Grep all occurrences of NL-101 / NL101 / nl101 across repo
    # -------------------------------------------------------------------------
    print("\n--- A.1: NL-101 / NL101 / nl101 OCCURRENCES ---")
    exts = {".py", ".html", ".js", ".json", ".csv", ".md", ".ipynb"}
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    nl101_hits = []
    pattern = re.compile(r"nl[-_]?101", re.IGNORECASE)

    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in exts:
                fpath = os.path.join(root, fn)
                relpath = os.path.relpath(fpath, REPO_DIR).replace("\\", "/")
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if pattern.search(line):
                                snippet = line.strip()[:220]
                                nl101_hits.append((relpath, idx, snippet))
                except Exception:
                    pass

    print(f"Total NL-101 hits across repo: {len(nl101_hits)}")
    for relpath, idx, snippet in nl101_hits:
        # Print all hits in code/data/html/notebooks, plus key md hits
        print(f"  {relpath}:{idx} -> {snippet}")

    # -------------------------------------------------------------------------
    # A.2: Check 16 Remediation Items across codebase
    # -------------------------------------------------------------------------
    print("\n--- A.2: CHECKING 16 REMEDIATION ITEMS ---")
    with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
        bs_lines = f.readlines()
    for i, l in enumerate(bs_lines, 1):
        if "0.999" in l:
            print(f"  [bridge_server.py:{i}] '0.999' hit: {l.strip()}")
        if "_validate_panel_against_table" in l:
            print(f"  [bridge_server.py:{i}] '_validate_panel_against_table': {l.strip()}")
        if "VERIFIED_SAFE" in l or "VERIFIED SAFE" in l or "approved for wet-lab" in l.lower():
            print(f"  [bridge_server.py:{i}] safety string: {l.strip()[:160]}")

    for html_fn in ["index.html", "how_it_works.html", "technical_catalog.html"]:
        if os.path.exists(html_fn):
            with open(html_fn, "r", encoding="utf-8", errors="ignore") as f:
                h_lines = f.readlines()
            for i, l in enumerate(h_lines, 1):
                for kw in ["VERIFIED SAFE", "VERIFIED_SAFE", "approved for wet-lab", "Harvard Genetic", "Adiv A. Johnson",
                           "scGPT", "CLINICAL+", "Phase 4", "GOLD VALIDATED", "v33.4_GOLD", "500M", "3.03B", "3.03 Billion",
                           "16 Attention", "16 attention", "2.42M", "2,420,000"]:
                    if kw.lower() in l.lower():
                        print(f"  [{html_fn}:{i}] '{kw}': {l.strip()[:160]}")

    # Check neuros_substrate_service.py
    for ns_path in ["services/neuros_substrate_service.py", "neuros_substrate_service.py"]:
        if os.path.exists(ns_path):
            with open(ns_path, "r", encoding="utf-8", errors="ignore") as f:
                ns_lines = f.readlines()
            print(f"Found {ns_path} ({len(ns_lines)} lines)")
            for i, l in enumerate(ns_lines, 1):
                if any(k in l for k in ["VERIFIED_SAFE", "gene_to_idx", "ion_expr", "gene_index", "var_names"]):
                    print(f"  [{ns_path}:{i}] {l.strip()[:160]}")

    # -------------------------------------------------------------------------
    # A.3: Filesystem-wide sweep for wet-lab files, >100MB data files, PERIHEART refs
    # -------------------------------------------------------------------------
    print("\n--- A.3: FILESYSTEM-WIDE SWEEP ---")
    wetlab_exts = {".fastq", ".fq", ".bam", ".sam", ".fcs", ".tif", ".tiff", ".czi", ".nd2", ".eds", ".rdml"}
    data_exts = {".h5ad", ".loom", ".rds", ".zarr", ".pt", ".pth", ".pkl"}
    wetlab_found = []
    large_data_found = []
    periheart_hits = []
    benchmark_hits = []

    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            fpath = os.path.join(root, fn)
            relpath = os.path.relpath(fpath, REPO_DIR).replace("\\", "/")
            ext = os.path.splitext(fn)[1].lower()
            try:
                sz = os.path.getsize(fpath)
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
            except Exception:
                sz, mtime = 0, "unknown"

            if ext in wetlab_exts or "fastq" in fn.lower():
                wetlab_found.append((relpath, sz, mtime))
            if ext in data_exts or sz >= 50 * 1024 * 1024:
                large_data_found.append((relpath, sz, mtime))

            if ext in {".py", ".ipynb", ".md", ".json", ".html"}:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                    for p_kw in ["f1606894", "PERIHEART", "Kanemaru"]:
                        if p_kw.lower() in txt.lower():
                            periheart_hits.append((relpath, p_kw))
                    for b_kw in ["99.8%", "98.2%", "280%", "0.982"]:
                        if b_kw in txt:
                            benchmark_hits.append((relpath, b_kw))
                except Exception:
                    pass

    print("Wet-lab files found:", wetlab_found)
    print("Data/model files found:")
    for rp, sz, mt in sorted(large_data_found, key=lambda x: -x[1]):
        print(f"  {rp:<65} | {sz/(1024*1024):>8.2f} MB | {mt}")
    print("PERIHEART references:", periheart_hits)
    print("Benchmark string references:", benchmark_hits)

    # -------------------------------------------------------------------------
    # A.4: Five Open Inconsistencies
    # -------------------------------------------------------------------------
    print("\n--- A.4: FIVE OPEN INCONSISTENCIES ---")
    # 1 & 3: zenith_foundation_v1 model.pt exact tensors and n_latent
    zf_ckpt = torch.load("models/zenith_foundation_v1/model.pt", map_location="cpu", weights_only=False)
    zf_sd = zf_ckpt["model_state_dict"]
    zf_total_params = sum(t.numel() for t in zf_sd.values())
    zf_float_params = sum(t.numel() for t in zf_sd.values() if t.is_floating_point())
    print(f"zenith_foundation_v1 model_state_dict tensors: {len(zf_sd)}")
    print(f"  All tensors numel sum:   {zf_total_params:,}")
    print(f"  Float tensors numel sum: {zf_float_params:,}")
    print(f"  init_params_: {zf_ckpt.get('attr_dict', {}).get('init_params_', {})}")
    for k, v in zf_sd.items():
        if "z_encoder" in k or "decoder" in k:
            print(f"    {k}: {tuple(v.shape)}")

    # 2: scvi_model_486k_real model.pt exact tensors
    sp_ckpt = torch.load("models/scvi_model_486k_real/model.pt", map_location="cpu", weights_only=False)
    sp_sd = sp_ckpt["model_state_dict"]
    sp_total_params = sum(t.numel() for t in sp_sd.values())
    sp_float_params = sum(t.numel() for t in sp_sd.values() if t.is_floating_point())
    print(f"scvi_model_486k_real model_state_dict tensors: {len(sp_sd)}")
    print(f"  All tensors numel sum:   {sp_total_params:,}")
    print(f"  Float tensors numel sum: {sp_float_params:,}")
    print(f"  init_params_: {sp_ckpt.get('attr_dict', {}).get('init_params_', {})}")
    for k, v in sp_sd.items():
        if not v.is_floating_point() or "px_r" in k or "z_encoder.mean" in k:
            print(f"    {k}: shape={tuple(v.shape)}, dtype={v.dtype}, numel={v.numel()}")

    # 5: Check synergy bonus in run_zenith_screening_pipeline.py and zenith_engine.py
    for pyf in ["run_zenith_screening_pipeline.py", "zenith_engine.py"]:
        if os.path.exists(pyf):
            with open(pyf, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    if any(w in line.lower() for w in ["synergy", "1.35", "1.65", "bonus"]):
                        print(f"  [{pyf}:{idx}] {line.strip()}")

    # -------------------------------------------------------------------------
    # A.5: PERIHEART Characterisation (Read-Only h5py on f1606894...h5ad)
    # -------------------------------------------------------------------------
    print("\n--- A.5: PERIHEART CHARACTERISATION (f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad) ---")
    ph_path = "data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad"
    f_ph = h5py.File(ph_path, "r")
    n_obs_ph = f_ph["X/indptr"].shape[0] - 1
    n_vars_ph = f_ph["X"].attrs.get("shape")[1]
    obs_cols_ph = list(f_ph["obs"].keys())
    var_cols_ph = list(f_ph["var"].keys())
    print(f"PERIHEART n_obs = {n_obs_ph:,}, n_vars = {n_vars_ph:,}")
    print(f"PERIHEART obs columns ({len(obs_cols_ph)}): {obs_cols_ph}")
    print(f"PERIHEART var columns ({len(var_cols_ph)}): {var_cols_ph}")

    def get_obs_col(h5f, col):
        obj = h5f[f"obs/{col}"]
        if isinstance(obj, h5py.Group) and "categories" in obj:
            cats = [x.decode("utf-8", errors="ignore") if isinstance(x, bytes) else str(x) for x in obj["categories"][:]]
            codes = obj["codes"][:]
            return np.array([cats[c] if c >= 0 else "NA" for c in codes])
        else:
            arr = obj[:]
            if arr.dtype.kind in {"S", "O"}:
                return np.array([x.decode("utf-8", errors="ignore") if isinstance(x, bytes) else str(x) for x in arr])
            return arr

    # Extract key columns in PERIHEART
    ph_df_dict = {}
    for c in obs_cols_ph:
        if c == "_index":
            continue
        try:
            ph_df_dict[c] = get_obs_col(f_ph, c)
        except Exception as e:
            print(f"  Could not load obs/{c}: {e}")

    df_ph_obs = pd.DataFrame(ph_df_dict)
    print("\nPERIHEART Cell Types:")
    ct_vc = df_ph_obs["cell_type"].value_counts()
    for k, v in ct_vc.items():
        print(f"  {k:<48}: {v:>8,} ({v/len(df_ph_obs)*100:5.2f}%)")

    # Compute per-cell total counts (UMI depth) and gene counts from X/indptr and X/data
    print("\nComputing PERIHEART per-donor sequencing depth & confound structure across all 54 donors...")
    indptr = f_ph["X/indptr"][:]
    n_genes_per_cell = np.diff(indptr)
    df_ph_obs["n_genes_detected"] = n_genes_per_cell

    # Map development_stage to numeric midpoint
    stage_to_age = {
        "fifth decade stage": 45.0,
        "sixth decade stage": 55.0,
        "seventh decade stage": 65.0,
        "eighth decade stage": 75.0,
        "ninth decade stage": 85.0,
    }
    df_ph_obs["age_midpoint"] = df_ph_obs["development_stage"].map(stage_to_age).astype(float)

    # Summarize all 54 donors
    donor_groups = df_ph_obs.groupby("donor_id")
    donor_rows = []
    for d_id, grp in donor_groups:
        row = {
            "donor_id": d_id,
            "development_stage": grp["development_stage"].iloc[0],
            "age_midpoint": float(grp["age_midpoint"].iloc[0]),
            "n_cells": len(grp),
            "n_vcm": int((grp["cell_type"].str.contains("ventricular", case=False) | (grp["cell_type"] == "cardiac muscle cell")).sum()),
            "n_reg_vcm": int((grp["cell_type"] == "regular ventricular cardiac myocyte").sum()),
            "n_cm_generic": int((grp["cell_type"] == "cardiac muscle cell").sum()),
            "n_fibroblast": int((grp["cell_type"] == "fibroblast").sum() + (grp["cell_type"] == "fibroblast of cardiac tissue").sum()),
            "median_genes": float( grp["n_genes_detected"].median()),
        }
        for cov in ["sex", "assay", "suspension_type", "tissue", "cell_enrichment", "author_batch_notes"]:
            if cov in grp.columns:
                vals = grp[cov].unique().tolist()
                row[cov] = vals[0] if len(vals) == 1 else f"Multiple({len(vals)}): {vals[:3]}"
        donor_rows.append(row)

    df_donors = pd.DataFrame(donor_rows).sort_values(["age_midpoint", "donor_id"]).reset_index(drop=True)
    df_donors.to_csv("scratch/phaseA5_periheart_54_donors.csv", index=False)
    print(f"\nSaved 54 PERIHEART donors to scratch/phaseA5_periheart_54_donors.csv:")
    print(df_donors.to_string(index=False))

    # Cross-tabulate development_stage vs technical covariates
    print("\n--- PERIHEART CONFOUND CROSS-TABULATION ---")
    for cov in ["sex", "assay", "suspension_type", "tissue", "cell_enrichment", "author_batch_notes"]:
        if cov in df_donors.columns:
            print(f"\nCross-tab development_stage vs {cov} (donor-level n=54):")
            ctab = pd.crosstab(df_donors["development_stage"], df_donors[cov])
            print(ctab)
            if ctab.shape[1] > 1:
                chi2, p_chi2, _, _ = stats.chi2_contingency(ctab)
                print(f"  Chi2 = {chi2:.4f}, p = {p_chi2:.4e}")

    r_genes, p_genes = stats.pearsonr(df_donors["age_midpoint"], df_donors["median_genes"])
    print(f"\nDonor age_midpoint vs median_genes (n=54): Pearson r = {r_genes:+.4f} (p = {p_genes:.4f})")

    # Gene identifier check & overlap with Litviňuková (d4e69e01...h5ad)
    f_lit = h5py.File("data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad", "r")
    ph_var_idx = [x.decode() if isinstance(x, bytes) else str(x) for x in f_ph["var/_index"][:]]
    lit_var_idx = [x.decode() if isinstance(x, bytes) else str(x) for x in f_lit["var/_index"][:]]
    ph_feat_names = [x.decode() if isinstance(x, bytes) else str(x) for x in f_ph["var/feature_name/categories"][f_ph["var/feature_name/codes"][:]]] if "feature_name" in f_ph["var"] else []
    lit_feat_names = [x.decode() if isinstance(x, bytes) else str(x) for x in f_lit["var/feature_name/categories"][f_lit["var/feature_name/codes"][:]]] if "feature_name" in f_lit["var"] else []

    overlap_ens = len(set(ph_var_idx) & set(lit_var_idx))
    overlap_sym = len(set(ph_feat_names) & set(lit_feat_names))
    print(f"\nPERIHEART var/_index sample: {ph_var_idx[:5]} (Ensembl IDs: {ph_var_idx[0].startswith('ENSG')})")
    print(f"Litvinukova var/_index sample: {lit_var_idx[:5]} (Ensembl IDs: {lit_var_idx[0].startswith('ENSG')})")
    print(f"Exact Ensembl ID overlap (PERIHEART {len(ph_var_idx):,} vs Litvinukova {len(lit_var_idx):,}): {overlap_ens:,} genes")
    print(f"Exact Symbol overlap (feature_name): {overlap_sym:,} genes")

if __name__ == "__main__":
    main()
