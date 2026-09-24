import os
import sys
import json
import math
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.stats as stats
import scvi

sys.stdout.reconfigure(encoding="utf-8")
np.random.seed(42)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADATA_PATH = os.path.join(REPO_DIR, "models", "scvi_model_hca", "adata.h5ad")
CT_GENES_PATH = os.path.join(REPO_DIR, "models", "cell_type_genes.json")
SCVI_MODEL_DIR = os.path.join(REPO_DIR, "models", "scvi_model_486k_real")
SCREEN_CSV_PATH = os.path.join(REPO_DIR, "screen_output.csv")
GRN_TSV_PATH = os.path.join(REPO_DIR, "models", "omnipath_collectri_dorothea_human.tsv")

DONOR_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5,
    "D5": 67.5, "D6": 72.5, "D7": 62.5, "D11": 62.5,
    "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5,
    "H6": 42.5, "H7": 47.5,
}

def fisher_ci(r, n=14):
    if abs(r) >= 0.9999:
        return (r, r)
    z = np.arctanh(r)
    se = 1.0 / math.sqrt(max(1, n - 3))
    z_low, z_high = z - 1.96 * se, z + 1.96 * se
    return (float(np.tanh(z_low)), float(np.tanh(z_high)))

def bh_adjust(pvals):
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    order = np.argsort(pvals)
    ranks = np.empty(n, dtype=int)
    ranks[order] = np.arange(1, n + 1)
    qvals = pvals * n / ranks
    # enforce monotonicity from largest to smallest
    qvals_sorted = qvals[order]
    for i in range(n - 2, -1, -1):
        qvals_sorted[i] = min(qvals_sorted[i], qvals_sorted[i + 1])
    qvals[order] = np.clip(qvals_sorted, 0.0, 1.0)
    return qvals

def main():
    print("=" * 75)
    print("RUNNING PHASE 3 (PROVENANCE) & PHASE 4 (STATISTICAL VALIDATION)")
    print("=" * 75)

    adata = sc.read_h5ad(ADATA_PATH)
    print(f"Loaded adata.h5ad: {adata.n_obs:,} cells x {adata.n_vars:,} genes")

    if "donor_id" not in adata.obs.columns:
        for cand in ["donor", "Donor", "sample", "donor_ID"]:
            if cand in adata.obs.columns:
                adata.obs["donor_id"] = adata.obs[cand].astype(str)
                break
    if "gene_name" not in adata.var.columns:
        for cand in ["feature_name", "gene_symbols", "symbol", "gene_short_name"]:
            if cand in adata.var.columns:
                adata.var["gene_name"] = adata.var[cand].astype(str)
                break
        else:
            adata.var["gene_name"] = [str(x) for x in adata.var_names]

    # Map donor ages
    adata.obs["donor_age"] = adata.obs["donor_id"].map(DONOR_AGE_MAP).astype(float)
    adata.obs["age_group"] = "middle"
    adata.obs.loc[adata.obs["donor_age"] <= 55.0, "age_group"] = "young"
    adata.obs.loc[adata.obs["donor_age"] >= 65.0, "age_group"] = "aged"

    # Build symbol -> column index and Ensembl -> column index maps in adata
    symbol_to_col = {}
    ensembl_to_col = {}
    ens_col_name = "gene_ids-Harvard-Nuclei" if "gene_ids-Harvard-Nuclei" in adata.var.columns else None
    for idx, sym in enumerate(adata.var_names):
        sym_str = str(sym)
        symbol_to_col[sym_str.upper()] = idx
        ensembl_to_col[sym_str] = idx
        if ens_col_name is not None:
            ens_val = str(adata.var[ens_col_name].iloc[idx])
            if ens_val and ens_val != "nan":
                ensembl_to_col[ens_val] = idx

    adata.var["gene_name"] = [str(x) for x in adata.var_names]

    # Load scvi_model_486k_real and compute 20-D latent coordinates on adata
    with open(os.path.join(SCVI_MODEL_DIR, "gene_index.json"), "r") as f:
        scvi_genes = json.load(f)["var_names"]

    # X in adata.h5ad is raw integer UMI counts; compute log1p(CP10k) for expression analysis
    X_counts = adata.X.toarray().astype(np.float32) if hasattr(adata.X, "toarray") else np.asarray(adata.X, dtype=np.float32)
    row_sums = np.maximum(X_counts.sum(axis=1, keepdims=True), 1.0)
    X_full = np.log1p((X_counts / row_sums) * 1e4)

    X_scvi = np.zeros((adata.n_obs, len(scvi_genes)), dtype=np.float32)
    for j, g_ens in enumerate(scvi_genes):
        if g_ens in ensembl_to_col:
            X_scvi[:, j] = X_counts[:, ensembl_to_col[g_ens]]

    adata_scvi = ad.AnnData(X=X_scvi, obs=adata.obs.copy(), var=pd.DataFrame(index=scvi_genes)) if "ad" in globals() else sc.AnnData(X=X_scvi, obs=adata.obs.copy(), var=pd.DataFrame(index=scvi_genes))
    scvi.model.SCVI.setup_anndata(adata_scvi)
    scvi_model = scvi.model.SCVI.load(SCVI_MODEL_DIR, adata=adata_scvi)
    latent_all = scvi_model.get_latent_representation()
    print(f"Computed 20-D scVI latent representations: shape={latent_all.shape}")

    with open(CT_GENES_PATH, "r", encoding="utf-8") as f:
        ct_json = json.load(f)

    donors_sorted = sorted(DONOR_AGE_MAP.keys())
    donor_ages_vec = np.array([DONOR_AGE_MAP[d] for d in donors_sorted], dtype=float)
    youth_ages_vec = -donor_ages_vec  # positive correlation with youth = negative correlation with chronological age

    results_summary = {"phase3": {}, "phase4": {}}

    # ── PHASE 3.3 & PHASE 4.1: Recompute vCM and Fibroblast Tables ──
    for ct_key, ct_name in [
        ("regular_ventricular_cardiac_myocyte", "Ventricular_Cardiomyocyte"),
        ("fibroblast", "Fibroblast")
    ]:
        mask = (adata.obs["cell_type"] == ct_name).values
        ct_X = X_full[mask]
        ct_lat = latent_all[mask]
        ct_obs = adata.obs.loc[mask]
        y_mask = (ct_obs["age_group"] == "young").values
        a_mask = (ct_obs["age_group"] == "aged").values
        y60_mask = (ct_obs["donor_age"] < 60.0).values
        a60_mask = (ct_obs["donor_age"] >= 60.0).values

        young_centroid = ct_lat[y_mask].mean(axis=0)
        aged_centroid = ct_lat[a_mask].mean(axis=0)
        rejuv_vec = young_centroid - aged_centroid
        proj = ct_lat @ rejuv_vec

        ct_info = ct_json["cell_types"][ct_key]
        table_genes = ct_info["pro_rejuvenation_genes"] + ct_info["aging_marker_genes"]

        rows = []
        for g_entry in table_genes:
            ens_id = g_entry["gene"]
            sym = g_entry.get("gene_symbol", ens_id)
            r_json = float(g_entry["correlation"])
            col_idx = ensembl_to_col.get(ens_id, symbol_to_col.get(sym.upper(), None))
            if col_idx is None:
                continue

            expr_cell = ct_X[:, col_idx]
            # 1. Recompute via exact extract_celltype_genes.py method (Pearson with scVI latent projection)
            r_proj, p_proj = stats.pearsonr(expr_cell, proj)
            # 2. Recompute via direct cell-level Pearson with youth (-donor_age)
            r_cell_youth, p_cell_youth = stats.pearsonr(expr_cell, -ct_obs["donor_age"].values)
            # 3. Group means
            mean_young_55 = float(expr_cell[y_mask].mean())
            mean_aged_65 = float(expr_cell[a_mask].mean())
            mean_young_60 = float(expr_cell[y60_mask].mean())
            mean_aged_60 = float(expr_cell[a60_mask].mean())

            # 4. Donor-level pseudobulk (14 donor means)
            donor_means = []
            valid_donor_ages = []
            for d in donors_sorted:
                d_mask = (ct_obs["donor_id"] == d).values
                if d_mask.sum() > 0:
                    donor_means.append(float(expr_cell[d_mask].mean()))
                    valid_donor_ages.append(DONOR_AGE_MAP[d])
            donor_means = np.array(donor_means)
            valid_donor_ages = np.array(valid_donor_ages)

            if np.std(donor_means) > 1e-12:
                # Correlate with youth (-valid_donor_ages) so sign matches r_json (+ = up in young, - = up in aged)
                r_donor_youth, p_donor = stats.pearsonr(donor_means, -valid_donor_ages)
                r_donor_age = -r_donor_youth
            else:
                r_donor_youth, p_donor, r_donor_age = 0.0, 1.0, 0.0

            ci_low, ci_high = fisher_ci(r_donor_youth, n=len(donor_means))

            rows.append({
                "symbol": sym,
                "ensembl": ens_id,
                "r_json": r_json,
                "r_local_scvi_proj": float(r_proj),
                "r_local_cell_youth": float(r_cell_youth),
                "r_donor_youth": float(r_donor_youth),
                "r_donor_chron_age": float(r_donor_age),
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "p_donor": float(p_donor),
                "mean_young_le55": mean_young_55,
                "mean_aged_ge65": mean_aged_65,
                "mean_young_lt60": mean_young_60,
                "mean_aged_ge60": mean_aged_60,
                "n_donors": int(len(donor_means)),
            })

        df_ct = pd.DataFrame(rows)
        df_ct["q_donor_bh"] = bh_adjust(df_ct["p_donor"].values)

        # Save full CSV
        out_csv = os.path.join(REPO_DIR, "scratch", f"phase3_4_{ct_key}_correlations.csv")
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        df_ct.to_csv(out_csv, index=False)

        # Compute summary stats
        r_json_vs_proj_p, _ = stats.pearsonr(df_ct["r_json"], df_ct["r_local_scvi_proj"])
        r_json_vs_proj_s, _ = stats.spearmanr(df_ct["r_json"], df_ct["r_local_scvi_proj"])
        r_json_vs_cell_p, _ = stats.pearsonr(df_ct["r_json"], df_ct["r_local_cell_youth"])
        r_json_vs_donor_p, _ = stats.pearsonr(df_ct["r_json"], df_ct["r_donor_youth"])
        r_json_vs_donor_s, _ = stats.spearmanr(df_ct["r_json"], df_ct["r_donor_youth"])

        n_sig_p05 = int((df_ct["p_donor"] < 0.05).sum())
        n_sig_q05 = int((df_ct["q_donor_bh"] < 0.05).sum())
        n_same_sign = int((np.sign(df_ct["r_json"]) == np.sign(df_ct["r_donor_youth"])).sum())

        results_summary["phase3"][ct_key] = {
            "n_genes": len(df_ct),
            "n_cells_local": int(mask.sum()),
            "n_young_le55": int(y_mask.sum()),
            "n_aged_ge65": int(a_mask.sum()),
            "pearson_json_vs_local_scvi_proj": float(r_json_vs_proj_p),
            "spearman_json_vs_local_scvi_proj": float(r_json_vs_proj_s),
            "pearson_json_vs_local_cell_youth": float(r_json_vs_cell_p),
            "pearson_json_vs_donor_youth": float(r_json_vs_donor_p),
            "spearman_json_vs_donor_youth": float(r_json_vs_donor_s),
            "n_donor_sig_p05": n_sig_p05,
            "n_donor_sig_q05": n_sig_q05,
            "n_same_sign_donor": n_same_sign,
        }
        print(f"\n[{ct_key}] ({len(df_ct)} genes, {mask.sum()} local cells):")
        print(f"  JSON r vs Local scVI Projection r: Pearson = {r_json_vs_proj_p:.4f}, Spearman = {r_json_vs_proj_s:.4f}")
        print(f"  JSON r vs Local Cell Youth r:      Pearson = {r_json_vs_cell_p:.4f}")
        print(f"  JSON r vs Donor Pseudobulk r(n=14): Pearson = {r_json_vs_donor_p:.4f}, Spearman = {r_json_vs_donor_s:.4f}")
        print(f"  Donor-level significant (p < 0.05): {n_sig_p05}/{len(df_ct)} | (BH q < 0.05): {n_sig_q05}/{len(df_ct)} | Same sign: {n_same_sign}/{len(df_ct)}")

        if ct_key == "fibroblast":
            for target_g in ["ADGRB3", "ABCA10", "NEGR1", "LAMB1", "PID1", "SPOCK1", "IRAK3"]:
                sub = df_ct[df_ct["symbol"] == target_g]
                if not sub.empty:
                    r0 = sub.iloc[0].to_dict()
                    print(f"  Fibroblast {target_g}: JSON_r={r0['r_json']:+.4f}, local_proj_r={r0['r_local_scvi_proj']:+.4f}, "
                          f"donor_r={r0['r_donor_youth']:+.4f} (p={r0['p_donor']:.3f}), "
                          f"mean_le55={r0['mean_young_le55']:.4f} vs mean_ge65={r0['mean_aged_ge65']:.4f}, "
                          f"mean_lt60={r0['mean_young_lt60']:.4f} vs mean_ge60={r0['mean_aged_ge60']:.4f}")

    # ── PHASE 4.2: Dissociation & Batch Confound (HSPB1, CRYAB vs QC metrics across 14 donors) ──
    print("\n" + "=" * 75)
    print("PHASE 4.2: DISSOCIATION & BATCH CONFOUND ANALYSIS (14 DONORS)")
    print("=" * 75)
    vcm_mask = (adata.obs["cell_type"] == "Ventricular_Cardiomyocyte").values
    vcm_X = X_full[vcm_mask]
    vcm_counts = X_counts[vcm_mask]
    vcm_obs = adata.obs.loc[vcm_mask].copy()

    # Identify MT genes
    mt_cols = [i for i, sym in enumerate(adata.var["gene_name"]) if str(sym).upper().startswith("MT-")]
    hspb1_col = symbol_to_col["HSPB1"]
    cryab_col = symbol_to_col["CRYAB"]
    ttnas1_col = symbol_to_col["TTN-AS1"]

    donor_qc_rows = []
    for d in donors_sorted:
        dm = (vcm_obs["donor_id"] == d).values
        c_sub = vcm_counts[dm]
        x_sub = vcm_X[dm]
        obs_sub = vcm_obs.iloc[np.where(dm)[0]]

        umi_per_cell = c_sub.sum(axis=1)
        genes_per_cell = (c_sub > 0).sum(axis=1)
        mt_pct_per_cell = (c_sub[:, mt_cols].sum(axis=1) / np.maximum(umi_per_cell, 1.0)) * 100.0

        site = "Sanger (D-series, DCD/DBD)" if d.startswith("D") else "Harvard (H-series, Nucleated)"
        source_col = str(obs_sub["cell_source"].iloc[0]) if "cell_source" in obs_sub.columns else site
        sex_val = str(obs_sub["sex"].iloc[0]) if "sex" in obs_sub.columns else (str(obs_sub["gender"].iloc[0]) if "gender" in obs_sub.columns else "Unknown")
        region_val = str(obs_sub["region"].iloc[0]) if "region" in obs_sub.columns else "Ventricular"

        donor_qc_rows.append({
            "donor_id": d,
            "age": DONOR_AGE_MAP[d],
            "age_group": "young_le55" if DONOR_AGE_MAP[d] <= 55 else ("aged_ge65" if DONOR_AGE_MAP[d] >= 65 else "middle_57_62"),
            "site_is_D": 1 if d.startswith("D") else 0,
            "site_label": source_col,
            "sex": sex_val,
            "region": region_val,
            "n_vcms": int(dm.sum()),
            "median_umi": float(np.median(umi_per_cell)),
            "median_genes": float(np.median(genes_per_cell)),
            "pct_mt": float(np.median(mt_pct_per_cell)),
            "HSPB1_mean": float(x_sub[:, hspb1_col].mean()),
            "CRYAB_mean": float(x_sub[:, cryab_col].mean()),
            "TTN_AS1_mean": float(x_sub[:, ttnas1_col].mean()),
        })

    df_qc = pd.DataFrame(donor_qc_rows)
    df_qc.to_csv(os.path.join(REPO_DIR, "scratch", "phase4_donor_qc_confound.csv"), index=False)
    print(df_qc[["donor_id", "age", "site_label", "sex", "n_vcms", "median_umi", "median_genes", "pct_mt", "HSPB1_mean", "CRYAB_mean"]].to_string(index=False))

    # Correlate HSPB1 & CRYAB donor means against age, site_is_D, median_umi, median_genes, pct_mt
    confound_stats = {}
    for marker in ["HSPB1_mean", "CRYAB_mean", "TTN_AS1_mean"]:
        y_vec = df_qc[marker].values
        confound_stats[marker] = {}
        for cov in ["age", "site_is_D", "median_umi", "median_genes", "pct_mt"]:
            r_val, p_val = stats.pearsonr(y_vec, df_qc[cov].values)
            confound_stats[marker][cov] = {"r": float(r_val), "p": float(p_val)}
            print(f"  {marker} vs {cov:<12}: r = {r_val:+.4f} (p = {p_val:.4f})")

        # Partial correlation / OLS regression adjusting for site_is_D and median_umi
        X_design = np.column_stack([
            np.ones(len(df_qc)),
            df_qc["age"].values,
            df_qc["site_is_D"].values,
            df_qc["median_umi"].values
        ])
        beta, _, _, _ = np.linalg.lstsq(X_design, y_vec, rcond=None)
        y_hat = X_design @ beta
        resid = y_vec - y_hat
        dof = len(df_qc) - X_design.shape[1]
        mse = np.sum(resid ** 2) / dof
        cov_beta = mse * np.linalg.inv(X_design.T @ X_design)
        se_beta = np.sqrt(np.diag(cov_beta))
        t_age = beta[1] / se_beta[1]
        p_age_adj = 2.0 * (1.0 - stats.t.cdf(abs(t_age), df=dof))
        t_site = beta[2] / se_beta[2]
        p_site_adj = 2.0 * (1.0 - stats.t.cdf(abs(t_site), df=dof))
        confound_stats[marker]["ols_adjusted"] = {
            "beta_age": float(beta[1]), "t_age": float(t_age), "p_age_adjusted": float(p_age_adj),
            "beta_site_D": float(beta[2]), "t_site_D": float(t_site), "p_site_D_adjusted": float(p_site_adj)
        }
        print(f"  {marker} OLS (adjusted for site + UMI depth): beta_age={beta[1]:+.4f} (t={t_age:+.2f}, p={p_age_adj:.4f}) | beta_site_D={beta[2]:+.4f} (t={t_site:+.2f}, p={p_site_adj:.4f})")

    results_summary["phase4"]["confound_stats"] = confound_stats

    # ── PHASE 4.3: False-Positive Calibration (500 Random Genes matched for detection frequency) ──
    print("\n" + "=" * 75)
    print("PHASE 4.3: FALSE-POSITIVE CALIBRATION (500 RANDOM FREQUENCY-MATCHED GENES)")
    print("=" * 75)
    det_freq = (vcm_X > 0).mean(axis=0)
    # Table genes in vCM have median detection frequency ~0.10 to 0.85; match random genes in [0.05, 0.90]
    eligible_random_cols = np.where((det_freq >= 0.05) & (det_freq <= 0.95))[0]
    np.random.seed(42)
    random_500_cols = np.random.choice(eligible_random_cols, size=500, replace=False)

    rand_r_list = []
    rand_p_list = []
    for c_idx in random_500_cols:
        d_means = np.array([vcm_X[(vcm_obs["donor_id"] == d).values, c_idx].mean() for d in donors_sorted])
        if np.std(d_means) > 1e-12:
            r_v, p_v = stats.pearsonr(d_means, -donor_ages_vec)
        else:
            r_v, p_v = 0.0, 1.0
        rand_r_list.append(abs(r_v))
        rand_p_list.append(p_v)

    rand_r_arr = np.array(rand_r_list)
    rand_p_arr = np.array(rand_p_list)
    rand_q_arr = bh_adjust(rand_p_arr)
    n_rand_p05 = int((rand_p_arr < 0.05).sum())
    n_rand_q05 = int((rand_q_arr < 0.05).sum())
    print(f"500 Random Genes at n=14 donors: {n_rand_p05}/500 ({n_rand_p05/5.0:.1f}%) reach p < 0.05 | {n_rand_q05}/500 reach BH q < 0.05")
    print(f"Random |r| percentiles: 50th={np.percentile(rand_r_arr, 50):.4f}, 90th={np.percentile(rand_r_arr, 90):.4f}, 95th={np.percentile(rand_r_arr, 95):.4f}, 99th={np.percentile(rand_r_arr, 99):.4f}")

    df_vcm_corr = pd.read_csv(os.path.join(REPO_DIR, "scratch", "phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv"))
    vcm_table_abs_r = df_vcm_corr["r_donor_youth"].abs().values
    print(f"vCM Table (100 genes) donor |r| percentiles: 50th={np.percentile(vcm_table_abs_r, 50):.4f}, 90th={np.percentile(vcm_table_abs_r, 90):.4f}, 95th={np.percentile(vcm_table_abs_r, 95):.4f}")

    results_summary["phase4"]["false_positive_calibration"] = {
        "n_random_genes": 500,
        "n_p_lt_005": n_rand_p05,
        "pct_p_lt_005": round(n_rand_p05 / 5.0, 2),
        "n_q_lt_005": n_rand_q05,
        "rand_abs_r_median": float(np.percentile(rand_r_arr, 50)),
        "rand_abs_r_95th": float(np.percentile(rand_r_arr, 95)),
        "vcm_table_abs_r_median": float(np.percentile(vcm_table_abs_r, 50)),
        "vcm_table_abs_r_95th": float(np.percentile(vcm_table_abs_r, 95)),
    }

    # ── PHASE 4.4: GRN Screen Null Distributions, Degree Regression & Quad Spread ──
    print("\n" + "=" * 75)
    print("PHASE 4.4: GRN SCREEN NULL DISTRIBUTIONS & DEGREE ARTIFACT TEST")
    print("=" * 75)
    df_screen = pd.read_csv(SCREEN_CSV_PATH)
    df_singles = df_screen[df_screen["n_factors"] == 1].copy()
    df_quads = df_screen[df_screen["n_factors"] == 4].copy()

    # Load GRN matrix and vCM young/aged vectors exactly as in run_part2_real_screen.py
    # Note: In our linear damped GRN propagation model with uniform dose=1.0 across a 4-TF set (damped by 1/sqrt(4) or additive),
    # let's load the exact GRN edges and compute the exact propagation score for 1,000 random 4-TF sets and 1,000 degree-matched 4-TF sets!
    grn_df = pd.read_csv(GRN_TSV_PATH, sep="\t")
    # Filter to genes in adata
    valid_syms = set(symbol_to_col.keys())
    grn_df["source_u"] = grn_df["source"].astype(str).str.upper()
    grn_df["target_u"] = grn_df["target"].astype(str).str.upper()
    grn_df = grn_df[grn_df["source_u"].isin(valid_syms) & grn_df["target_u"].isin(valid_syms)].copy()

    # We can also check single-TF scores and degrees directly from df_singles (238 TFs)!
    print(f"Loaded {len(df_singles)} single TFs and {len(df_quads)} 4-TF quads from screen_output.csv")

    # (b) Degree correlation across all 238 single TFs
    deg_vec = df_singles["n_active_edges"].values.astype(float)
    score_vec = df_singles["youth_restoration_excl_pct"].values.astype(float)
    r_deg_p, p_deg_p = stats.pearsonr(deg_vec, score_vec)
    r_deg_s, p_deg_s = stats.spearmanr(deg_vec, score_vec)
    log_deg = np.log10(deg_vec + 1.0)
    r_logdeg_p, p_logdeg_p = stats.pearsonr(log_deg, score_vec)
    r2_logdeg = r_logdeg_p ** 2

    # Regress score on log10(degree + 1) and abs_score on log10(degree + 1)
    slope, intercept, _, _, _ = stats.linregress(log_deg, score_vec)
    df_singles["expected_from_log_deg"] = intercept + slope * log_deg
    df_singles["residual_score"] = score_vec - df_singles["expected_from_log_deg"]

    # Also check correlation between out-degree and POSITIVE score (>0) or |score|
    r_abs_deg_p, p_abs_deg_p = stats.pearsonr(log_deg, np.abs(score_vec))
    pos_singles = df_singles[df_singles["youth_restoration_excl_pct"] > 0].copy()
    r_pos_deg_p, p_pos_deg_p = stats.pearsonr(np.log10(pos_singles["n_active_edges"] + 1.0), pos_singles["youth_restoration_excl_pct"])

    print(f"[4.4b] Single-TF (n=238) Out-Degree vs Score: Pearson r = {r_deg_p:+.4f} (p={p_deg_p:.4e}), Spearman rho = {r_deg_s:+.4f} (p={p_deg_s:.4e})")
    print(f"[4.4b] log10(Out-Degree) vs Score: Pearson r = {r_logdeg_p:+.4f} (R^2 = {r2_logdeg:.4f}, p={p_logdeg_p:.4e})")
    print(f"[4.4b] log10(Out-Degree) vs |Score| (magnitude): Pearson r = {r_abs_deg_p:+.4f} (R^2 = {r_abs_deg_p**2:.4f}, p={p_abs_deg_p:.4e})")
    print(f"[4.4b] Among positive TFs (n={len(pos_singles)}), log10(Out-Degree) vs Score: Pearson r = {r_pos_deg_p:+.4f} (R^2 = {r_pos_deg_p**2:.4f}, p={p_pos_deg_p:.4e})")

    # Now let's run the exact 4-TF GRN propagation for:
    # (1) 1,000 random 4-TF sets from the 238 qualifying TFs
    # (2) 1,000 degree-matched 4-TF sets (total active edges within +/-10% of winner's 748 edges: [673, 823])
    # Using the exact young (<60y) vs aged (>=60y) vCM profiles and GRN transition matrix from run_part2_real_screen.py!
    y60_vcm = vcm_X[(vcm_obs["donor_age"] < 60.0).values].mean(axis=0)
    a60_vcm = vcm_X[(vcm_obs["donor_age"] >= 60.0).values].mean(axis=0)
    diff_ya = y60_vcm - a60_vcm
    # Genes with |young - aged| > 0.01 (aging signature genes)
    sig_mask = np.abs(diff_ya) > 0.01

    # Build per-TF delta vector in vCMs (matching run_part2_real_screen.py)
    tf_list = df_singles["combination"].tolist()
    tf_deg_map = dict(zip(df_singles["combination"], df_singles["n_active_edges"]))
    tf_score_map = dict(zip(df_singles["combination"], df_singles["youth_restoration_excl_pct"]))

    # Notice how 4-TF quad score in run_part2_real_screen.py relates to single-TF shifts:
    # Let's check on the 211 quads how quad score relates to sum of single-TF scores / sqrt(4)!
    quad_check = []
    for _, qrow in df_quads.iterrows():
        tfs = qrow["combination"].split("+")
        if all(t in tf_score_map for t in tfs):
            s_sum = sum(tf_score_map[t] for t in tfs) / math.sqrt(4.0)
            quad_check.append((qrow["youth_restoration_excl_pct"], s_sum))
    if quad_check:
        q_actual, q_pred = zip(*quad_check)
        print(f"  Verification of quad propagation formula r(actual, exact_propagation) = {stats.pearsonr(q_actual, q_pred)[0]:.6f}")

    # Build exact TF -> target adjacency dictionary from grn_df for exact circularity-free evaluation
    tf_edges = {}
    for tf_sym in tf_list:
        sub_e = grn_df[grn_df["source_u"] == tf_sym]
        edges_list = []
        for _, erow in sub_e.iterrows():
            t_idx = symbol_to_col[erow["target_u"]]
            if vcm_X[:, t_idx].mean() > 0.005 or a60_vcm[t_idx] > 0.005:
                edges_list.append((t_idx, float(erow["mor"])))
        tf_edges[tf_sym] = edges_list

    def eval_quad_exact(tfs_tuple):
        # Compute exact circularity-free youth restoration pct & active edges
        perturbed = a60_vcm.copy()
        tf_indices = {symbol_to_col[t] for t in tfs_tuple if t in symbol_to_col}
        total_edges = 0
        scale = 0.15 / math.sqrt(len(tfs_tuple))
        for t in tfs_tuple:
            e_list = tf_edges.get(t, [])
            total_edges += len(e_list)
            for t_idx, mor in e_list:
                perturbed[t_idx] = max(0.0, perturbed[t_idx] + scale * mor * max(0.2, a60_vcm[t_idx]))
        eval_mask = sig_mask.copy()
        for idx in tf_indices:
            eval_mask[idx] = False
        d0 = np.linalg.norm(a60_vcm[eval_mask] - y60_vcm[eval_mask])
        d1 = np.linalg.norm(perturbed[eval_mask] - y60_vcm[eval_mask])
        score_pct = ((d0 - d1) / d0) * 100.0
        return score_pct, total_edges

    winner_tfs = ("NFKB1", "MITF", "CTCF", "HIF1A")
    winner_score, winner_edges = eval_quad_exact(winner_tfs)
    print(f"  Winner {winner_tfs}: exact score = {winner_score:+.4f}%, edges = {winner_edges}")

    # 1,000 Random 4-TF sets from the 238 TFs
    np.random.seed(42)
    rand_quad_scores = []
    rand_quad_edges = []
    for _ in range(1000):
        chosen = tuple(np.random.choice(tf_list, size=4, replace=False))
        sc_val, ed_val = eval_quad_exact(chosen)
        rand_quad_scores.append(sc_val)
        rand_quad_edges.append(ed_val)
    rand_quad_scores = np.array(rand_quad_scores)

    # 1,000 Degree-Matched 4-TF sets (total edges in [673, 823], i.e. 748 +/- 10%)
    # Since random 4-TF sets from 238 TFs have lower average degree (~120 edges), we sample from higher-degree TFs to match [673, 823]
    high_deg_pool = [t for t in tf_list if len(tf_edges.get(t, [])) >= 50]
    deg_matched_scores = []
    deg_matched_edges = []
    attempts = 0
    while len(deg_matched_scores) < 1000 and attempts < 50000:
        attempts += 1
        pool = high_deg_pool if attempts < 25000 else tf_list
        chosen = tuple(np.random.choice(pool, size=4, replace=False))
        if set(chosen) == set(winner_tfs):
            continue
        ed_sum = sum(len(tf_edges.get(t, [])) for t in chosen)
        if int(winner_edges * 0.90) <= ed_sum <= int(winner_edges * 1.10):
            sc_val, _ = eval_quad_exact(chosen)
            deg_matched_scores.append(sc_val)
            deg_matched_edges.append(ed_sum)
    deg_matched_scores = np.array(deg_matched_scores)

    print(f"[4.4a] Random 4-TF Null (n=1000): mean={rand_quad_scores.mean():+.4f}%, SD={rand_quad_scores.std():.4f}%, "
          f"positive={(rand_quad_scores > 0).sum()}/1000, 95th={np.percentile(rand_quad_scores, 95):+.4f}%, max={rand_quad_scores.max():+.4f}%")
    p_emp_random = float((rand_quad_scores >= winner_score).sum() / len(rand_quad_scores))
    pct_random = float((rand_quad_scores < winner_score).mean() * 100.0)
    print(f"       Winner (+6.069%) vs Random Null: percentile={pct_random:.2f}%, empirical p={p_emp_random:.4f}")

    print(f"[4.4a] Degree-Matched 4-TF Null (n={len(deg_matched_scores)}, edges in [{int(winner_edges*0.9)}, {int(winner_edges*1.1)}]): "
          f"mean={deg_matched_scores.mean():+.4f}%, SD={deg_matched_scores.std():.4f}%, "
          f"positive={(deg_matched_scores > 0).sum()}/{len(deg_matched_scores)}, 95th={np.percentile(deg_matched_scores, 95):+.4f}%, max={deg_matched_scores.max():+.4f}%")
    p_emp_deg = float((deg_matched_scores >= winner_score).sum() / len(deg_matched_scores))
    pct_deg = float((deg_matched_scores < winner_score).mean() * 100.0)
    print(f"       Winner (+6.069%) vs Degree-Matched Null: percentile={pct_deg:.2f}%, empirical p={p_emp_deg:.4f}")

    # Regress all 211 Quads on log10(n_active_edges) and check if NFKB1+MITF+CTCF+HIF1A survives residual re-ranking!
    q_log_deg = np.log10(df_quads["n_active_edges"].values.astype(float) + 1.0)
    q_scores = df_quads["youth_restoration_excl_pct"].values.astype(float)
    q_slope, q_int, q_r, q_p, _ = stats.linregress(q_log_deg, q_scores)
    df_quads["degree_residual"] = q_scores - (q_int + q_slope * q_log_deg)
    df_quads_res_sorted = df_quads.sort_values("degree_residual", ascending=False).reset_index(drop=True)
    winner_res_rank = int(df_quads_res_sorted[df_quads_res_sorted["combination"] == "NFKB1+MITF+CTCF+HIF1A"].index[0]) + 1
    print(f"[4.4b] Across 211 Quads, log10(degree) R^2 = {q_r**2:.4f} (r={q_r:+.4f}, p={q_p:.4e}).")
    print(f"       Winner NFKB1+MITF+CTCF+HIF1A rank after regressing out log(degree): Rank #{winner_res_rank} / 211!")
    print("       Top 5 Quads by Degree-Adjusted Residual:")
    for idx_r in range(5):
        r_row = df_quads_res_sorted.iloc[idx_r]
        print(f"         #{idx_r+1}: {r_row['combination']} | raw={r_row['youth_restoration_excl_pct']:+.3f}% | edges={int(r_row['n_active_edges'])} | residual={r_row['degree_residual']:+.3f}%")

    # (c) Spread across all 211 quads: how many fall inside winner's 95% CI [5.765, 6.249]?
    n_in_ci = int(((q_scores >= 5.765) & (q_scores <= 6.249)).sum())
    print(f"[4.4c] Quads inside winner's 95% CI ([+5.765%, +6.249%]): {n_in_ci} / 211 (Top 5 quads: {q_scores[:5].round(3).tolist()})")

    results_summary["phase4"]["grn_screen"] = {
        "single_tf_pearson_r_deg": float(r_deg_p),
        "single_tf_spearman_r_deg": float(r_deg_s),
        "single_tf_log_deg_r2": float(r2_logdeg),
        "single_tf_abs_score_log_deg_r": float(r_abs_deg_p),
        "pos_single_tf_log_deg_r": float(r_pos_deg_p),
        "pos_single_tf_log_deg_r2": float(r_pos_deg_p ** 2),
        "quad_log_deg_r": float(q_r),
        "quad_log_deg_r2": float(q_r ** 2),
        "winner_residual_rank_quads": winner_res_rank,
        "random_4tf_null": {
            "mean": float(rand_quad_scores.mean()),
            "sd": float(rand_quad_scores.std()),
            "p5": float(np.percentile(rand_quad_scores, 5)),
            "p50": float(np.percentile(rand_quad_scores, 50)),
            "p95": float(np.percentile(rand_quad_scores, 95)),
            "max": float(rand_quad_scores.max()),
            "n_positive": int((rand_quad_scores > 0).sum()),
            "n_negative": int((rand_quad_scores < 0).sum()),
            "winner_percentile": pct_random,
            "winner_empirical_p": p_emp_random,
        },
        "degree_matched_4tf_null": {
            "n_samples": int(len(deg_matched_scores)),
            "mean": float(deg_matched_scores.mean()),
            "sd": float(deg_matched_scores.std()),
            "p5": float(np.percentile(deg_matched_scores, 5)),
            "p50": float(np.percentile(deg_matched_scores, 50)),
            "p95": float(np.percentile(deg_matched_scores, 95)),
            "max": float(deg_matched_scores.max()),
            "n_positive": int((deg_matched_scores > 0).sum()),
            "n_negative": int((deg_matched_scores < 0).sum()),
            "winner_percentile": pct_deg,
            "winner_empirical_p": p_emp_deg,
        },
        "quads_in_winner_95ci": n_in_ci,
    }

    with open(os.path.join(REPO_DIR, "scratch", "phase3_4_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print("\nSaved complete Phase 3 & Phase 4 summary to scratch/phase3_4_summary.json")

if __name__ == "__main__":
    main()
