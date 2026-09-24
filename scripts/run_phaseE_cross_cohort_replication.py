"""
Phase E: Independent Cross-Cohort Donor-Level Replication Analysis
Cohort 1: Litvinukova et al. (Nature 2020) Full 486,134-cell HCA Atlas (14 donors)
Cohort 2: PERIHEART Kanemaru et al. (Nature 2023) Full 392,819-cell Atlas (54 donors)

Computes per-donor log2(CP10k + 1) pseudobulk profiles in streaming CSR chunks,
evaluates Pearson r, Spearman rho, 95% Fisher z CIs, two-sided p, BH q,
500-gene detection-frequency-matched empirical nulls per cohort,
replication intersections, binomial overlap p-values, and secondary covariate-adjusted OLS.
"""
import json
import time
import h5py
import numpy as np
import pandas as pd
from scipy import stats

SEED = 42
np.random.seed(SEED)

LIT_PATH = "data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad"
PERI_PATH = "data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad"
TABLE_PATH = "models/cell_type_genes.json"

LIT_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5, "D5": 67.5, "D6": 72.5, "D7": 62.5,
    "D11": 62.5, "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5, "H6": 42.5, "H7": 47.5
}

PERI_STAGE_MAP = {
    "fifth decade stage": 45.0,
    "sixth decade stage": 55.0,
    "seventh decade stage": 65.0,
    "eighth decade stage": 75.0,
    "ninth decade stage": 85.0,
}


def decode_cat(grp):
    cats = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in grp["categories"][:]]
    codes = grp["codes"][:]
    return np.array([cats[c] if c >= 0 else "" for c in codes], dtype=object)


def stream_pseudobulk_h5ad(h5_path, donor_col, celltype_col, target_celltypes, chunk_size=25000):
    """
    Streams CSR matrix from h5ad in row chunks of `chunk_size` cells.
    Detect whether X is already log-normalized or raw counts; if raw counts, applies log2(CP10k + 1).
    Returns:
      ensembl_ids, gene_symbols, donor_pseudobulk[ct][donor] = (mean_vec, n_cells), expr_frac[ct] = frac_detected_vec
    """
    t0 = time.time()
    with h5py.File(h5_path, "r") as f:
        ens_ids = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in f["var"]["_index"][:]]
        if "feature_name" in f["var"]:
            sym_arr = decode_cat(f["var"]["feature_name"])
        else:
            sym_arr = np.array(ens_ids, dtype=object)

        donors = decode_cat(f["obs"][donor_col])
        celltypes = decode_cat(f["obs"][celltype_col])
        n_obs = len(donors)
        n_vars = len(ens_ids)

        # Check X vs raw/X to see if X is already log1p normalized or raw counts
        x_grp = f["X"]
        indptr = x_grp["indptr"][:]
        sample_data = x_grp["data"][:10000]
        is_already_log = bool(np.max(sample_data) < 25.0 and np.any(np.mod(sample_data, 1.0) != 0))
        print(f"[{h5_path.split('/')[-1]}] n_obs={n_obs}, n_vars={n_vars}, is_already_log={is_already_log}")

        # Initialize accumulators per target celltype and donor
        unique_donors = sorted(list(set(donors)))
        sums = {ct: {d: np.zeros(n_vars, dtype=np.float64) for d in unique_donors} for ct in target_celltypes}
        counts = {ct: {d: 0 for d in unique_donors} for ct in target_celltypes}
        detected_cells = {ct: np.zeros(n_vars, dtype=np.int64) for ct in target_celltypes}
        total_ct_cells = {ct: 0 for ct in target_celltypes}

        target_set = set(target_celltypes)

        for start in range(0, n_obs, chunk_size):
            end = min(start + chunk_size, n_obs)
            chunk_cts = celltypes[start:end]
            # Check if any cell in chunk belongs to target_set
            mask_in_target = np.isin(chunk_cts, list(target_set))
            if not np.any(mask_in_target):
                continue

            p_start = indptr[start]
            p_end = indptr[end]
            data_chunk = x_grp["data"][p_start:p_end].astype(np.float32)
            indices_chunk = x_grp["indices"][p_start:p_end]
            local_indptr = indptr[start:end + 1] - p_start

            # If raw counts, normalize each cell to log2(CP10k + 1)
            if not is_already_log:
                row_lengths = np.diff(local_indptr)
                row_ids = np.repeat(np.arange(end - start), row_lengths)
                row_sums = np.bincount(row_ids, weights=data_chunk, minlength=end - start).astype(np.float32)
                row_sums[row_sums == 0] = 1.0
                scale_factors = (10000.0 / row_sums)[row_ids]
                data_chunk = np.log2(data_chunk * scale_factors + 1.0)

            chunk_donors = donors[start:end]
            for ct in target_celltypes:
                ct_rows = np.where(chunk_cts == ct)[0]
                if len(ct_rows) == 0:
                    continue
                total_ct_cells[ct] += len(ct_rows)
                # Group by donor inside this chunk
                ct_donors = chunk_donors[ct_rows]
                for d in np.unique(ct_donors):
                    d_rows = ct_rows[ct_donors == d]
                    counts[ct][d] += len(d_rows)
                    # Collect slices for d_rows
                    for r in d_rows:
                        s_i, e_i = local_indptr[r], local_indptr[r + 1]
                        cols = indices_chunk[s_i:e_i]
                        vals = data_chunk[s_i:e_i]
                        sums[ct][d][cols] += vals
                        detected_cells[ct][cols] += 1

        print(f"  Finished streaming {h5_path.split('/')[-1]} in {time.time() - t0:.1f}s")
        pseudobulk = {}
        expr_frac = {}
        for ct in target_celltypes:
            pseudobulk[ct] = {}
            for d in unique_donors:
                if counts[ct][d] >= 10:  # Require at least 10 cells of that lineage in donor
                    pseudobulk[ct][d] = (sums[ct][d] / float(counts[ct][d]), counts[ct][d])
            expr_frac[ct] = detected_cells[ct] / float(max(1, total_ct_cells[ct]))

        return ens_ids, sym_arr, pseudobulk, expr_frac


def compute_donor_correlations(pseudobulk_dict, age_map, expr_frac_vec, min_detect_frac=0.05):
    """
    Computes continuous donor-level Pearson r and Spearman rho vs YOUTH (-age),
    so that r > 0 means higher in young donors (matching models/cell_type_genes.json)
    and r < 0 means higher in aged donors.
    Also computes the 500-gene matched-random empirical null (5% <= detection <= 95%).
    """
    donors = sorted([d for d in pseudobulk_dict.keys() if d in age_map])
    n_donors = len(donors)
    ages = np.array([age_map[d] for d in donors], dtype=np.float64)
    youth = -ages  # Positive r = youth-associated, Negative r = aging-associated

    mat = np.vstack([pseudobulk_dict[d][0] for d in donors])  # (n_donors, n_genes)

    # Vectorized Pearson r across all genes
    y_centered = youth - youth.mean()
    y_norm = np.sqrt(np.sum(y_centered ** 2))
    m_centered = mat - mat.mean(axis=0, keepdims=True)
    m_norm = np.sqrt(np.sum(m_centered ** 2, axis=0))
    valid_var = m_norm > 1e-12

    r_pearson = np.zeros(mat.shape[1], dtype=np.float64)
    r_pearson[valid_var] = (y_centered @ m_centered[:, valid_var]) / (y_norm * m_norm[valid_var])
    r_pearson = np.clip(r_pearson, -0.999999, 0.999999)

    # Two-sided t-test p-values
    df_deg = n_donors - 2
    t_stat = r_pearson * np.sqrt(df_deg / (1.0 - r_pearson ** 2))
    p_vals = 2.0 * stats.t.sf(np.abs(t_stat), df=df_deg)
    p_vals[~valid_var] = 1.0

    # Fisher z 95% CI
    z_val = np.arctanh(r_pearson)
    se_z = 1.0 / np.sqrt(max(1, n_donors - 3))
    ci_low = np.tanh(z_val - 1.96 * se_z)
    ci_high = np.tanh(z_val + 1.96 * se_z)

    # Active genes filter (>= 5% detection)
    active_mask = (expr_frac_vec >= min_detect_frac) & valid_var
    active_indices = np.where(active_mask)[0]

    # Benjamini-Hochberg FDR across active genes
    q_vals = np.ones_like(p_vals)
    if len(active_indices) > 0:
        p_act = p_vals[active_indices]
        order = np.argsort(p_act)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(p_act) + 1)
        q_act = p_act * len(p_act) / ranks
        # Enforce monotonicity
        q_act_sorted = np.minimum.accumulate(q_act[order][::-1])[::-1]
        q_act_final = np.empty_like(q_act)
        q_act_final[order] = np.clip(q_act_sorted, 0.0, 1.0)
        q_vals[active_indices] = q_act_final

    # Spearman rho for active genes
    rank_youth = stats.rankdata(youth)
    ry_c = rank_youth - rank_youth.mean()
    ry_n = np.sqrt(np.sum(ry_c ** 2))
    rho_spearman = np.zeros_like(r_pearson)
    for idx in active_indices:
        rg = stats.rankdata(mat[:, idx])
        rg_c = rg - rg.mean()
        rg_n = np.sqrt(np.sum(rg_c ** 2))
        if rg_n > 1e-12:
            rho_spearman[idx] = np.dot(ry_c, rg_c) / (ry_n * rg_n)

    # Matched-random empirical null: 500 random genes with 5% <= expr_frac <= 95%
    pool_indices = np.where((expr_frac_vec >= 0.05) & (expr_frac_vec <= 0.95) & valid_var)[0]
    rng = np.random.default_rng(SEED)
    sampled_null = rng.choice(pool_indices, size=min(500, len(pool_indices)), replace=False)
    null_abs_r = np.abs(r_pearson[sampled_null])
    null_p = p_vals[sampled_null]
    null_q = q_vals[sampled_null]

    null_summary = {
        "n_donors": n_donors,
        "n_active_genes": int(len(active_indices)),
        "n_null_genes": int(len(sampled_null)),
        "fpr_p_lt_005_count": int(np.sum(null_p < 0.05)),
        "fpr_p_lt_005_pct": round(float(np.mean(null_p < 0.05) * 100.0), 2),
        "bh_q_lt_005_count": int(np.sum(null_q < 0.05)),
        "bh_q_lt_005_pct": round(float(np.mean(null_q < 0.05) * 100.0), 2),
        "p50_abs_r": round(float(np.percentile(null_abs_r, 50)), 4),
        "p90_abs_r": round(float(np.percentile(null_abs_r, 90)), 4),
        "p95_abs_r": round(float(np.percentile(null_abs_r, 95)), 4),
        "p99_abs_r": round(float(np.percentile(null_abs_r, 99)), 4),
        "critical_r_p005": round(float(stats.t.ppf(0.975, df=df_deg) / np.sqrt(df_deg + stats.t.ppf(0.975, df=df_deg)**2)), 4),
    }

    return {
        "donors": donors,
        "ages": ages,
        "mat": mat,
        "r_pearson": r_pearson,
        "rho_spearman": rho_spearman,
        "p_vals": p_vals,
        "q_vals": q_vals,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "active_mask": active_mask,
        "null_summary": null_summary,
    }


def main():
    print("=" * 80)
    print("PHASE E — INDEPENDENT CROSS-COHORT REPLICATION (LITVINUKOVA n=14 vs PERIHEART n=54)")
    print("=" * 80)

    import os, pickle
    cache_file = "scratch/phaseE_pseudobulk_cache.pkl"
    if os.path.exists(cache_file):
        print(f"Loading cached pseudobulk matrices from {cache_file}...")
        with open(cache_file, "rb") as cf:
            lit_ens, lit_syms, lit_pb, lit_frac, peri_ens, peri_syms, peri_pb, peri_frac = pickle.load(cf)
    else:
        lit_ens, lit_syms, lit_pb, lit_frac = stream_pseudobulk_h5ad(
            LIT_PATH, "donor_id", "cell_type",
            ["regular ventricular cardiac myocyte", "regular atrial cardiac myocyte", "fibroblast"]
        )
        peri_ens, peri_syms, peri_pb, peri_frac = stream_pseudobulk_h5ad(
            PERI_PATH, "donor_id", "cell_type",
            ["cardiac muscle cell", "fibroblast"]
        )
        with open(cache_file, "wb") as cf:
            pickle.dump((lit_ens, lit_syms, lit_pb, lit_frac, peri_ens, peri_syms, peri_pb, peri_frac), cf)

    # Build PERIHEART donor -> age_midpoint map from obs
    with h5py.File(PERI_PATH, "r") as f:
        p_donors = decode_cat(f["obs"]["donor_id"])
        p_stages = decode_cat(f["obs"]["development_stage"])
    peri_age_map = {}
    for d, st in zip(p_donors, p_stages):
        if d not in peri_age_map and st in PERI_STAGE_MAP:
            peri_age_map[d] = PERI_STAGE_MAP[st]

    # Run per-cohort independent analyses
    res_lit_vcm = compute_donor_correlations(
        lit_pb["regular ventricular cardiac myocyte"], LIT_AGE_MAP, lit_frac["regular ventricular cardiac myocyte"]
    )
    res_lit_acm = compute_donor_correlations(
        lit_pb["regular atrial cardiac myocyte"], LIT_AGE_MAP, lit_frac["regular atrial cardiac myocyte"]
    )
    res_lit_fib = compute_donor_correlations(
        lit_pb["fibroblast"], LIT_AGE_MAP, lit_frac["fibroblast"]
    )

    res_peri_cm = compute_donor_correlations(
        peri_pb["cardiac muscle cell"], peri_age_map, peri_frac["cardiac muscle cell"]
    )
    res_peri_fib = compute_donor_correlations(
        peri_pb["fibroblast"], peri_age_map, peri_frac["fibroblast"]
    )

    print("\n=== EMPIRICAL RANDOM-GENE NULL COMPARISON PER COHORT ===")
    for label, res in [
        ("Litvinukova vCM (n=14)", res_lit_vcm),
        ("Litvinukova aCM (n=12)", res_lit_acm),
        ("Litvinukova Fibroblast (n=14)", res_lit_fib),
        ("PERIHEART Atrial CM (n=54)", res_peri_cm),
        ("PERIHEART Fibroblast (n=54)", res_peri_fib),
    ]:
        ns = res["null_summary"]
        print(f"  {label:<32}: FPR(p<0.05)={ns['fpr_p_lt_005_count']}/500 ({ns['fpr_p_lt_005_pct']:.1f}%) | "
              f"95th_pct_|r|={ns['p95_abs_r']:.4f} | crit_r(p<0.05)={ns['critical_r_p005']:.4f}")

    # Align shared Ensembl IDs across both cohorts
    lit_idx_map = {e: i for i, e in enumerate(lit_ens)}
    peri_idx_map = {e: i for i, e in enumerate(peri_ens)}
    shared_ens = [e for e in lit_ens if e in peri_idx_map]
    lit_shared_i = np.array([lit_idx_map[e] for e in shared_ens])
    peri_shared_i = np.array([peri_idx_map[e] for e in shared_ens])
    shared_syms = np.array([lit_syms[i] for i in lit_shared_i])

    def analyze_intersection(name, r1_dict, r2_dict, table_genes_list=None):
        mask_both_active = r1_dict["active_mask"][lit_shared_i] & r2_dict["active_mask"][peri_shared_i]
        idx_active = np.where(mask_both_active)[0]
        n_shared_active = len(idx_active)

        r1 = r1_dict["r_pearson"][lit_shared_i][idx_active]
        r2 = r2_dict["r_pearson"][peri_shared_i][idx_active]
        p1 = r1_dict["p_vals"][lit_shared_i][idx_active]
        p2 = r2_dict["p_vals"][peri_shared_i][idx_active]
        syms = shared_syms[idx_active]
        ens_sub = np.array(shared_ens)[idx_active]

        thr1_emp95 = r1_dict["null_summary"]["p95_abs_r"]
        thr2_emp95 = r2_dict["null_summary"]["p95_abs_r"]

        # 1. Cohort-specific 95th-percentile empirical null threshold in BOTH cohorts
        pass1_emp = np.abs(r1) > thr1_emp95
        pass2_emp = np.abs(r2) > thr2_emp95
        both_emp = pass1_emp & pass2_emp
        both_emp_concordant = both_emp & (np.sign(r1) == np.sign(r2))

        # Binomial test for empirical-95th overlap under independence
        p_marginal_1 = np.mean(pass1_emp)
        p_marginal_2 = np.mean(pass2_emp)
        expected_overlap_emp = n_shared_active * p_marginal_1 * p_marginal_2
        binom_p_emp = float(stats.binomtest(int(np.sum(both_emp)), n=n_shared_active, p=max(1e-9, p_marginal_1 * p_marginal_2), alternative="greater").pvalue)
        # Sign-concordant binomial test (probability of both passing AND same sign = 0.5 * p1 * p2)
        binom_p_emp_concord = float(stats.binomtest(int(np.sum(both_emp_concordant)), n=n_shared_active, p=max(1e-9, 0.5 * p_marginal_1 * p_marginal_2), alternative="greater").pvalue)

        # 2. Nominal p < 0.05 in BOTH cohorts
        pass1_nom = p1 < 0.05
        pass2_nom = p2 < 0.05
        both_nom = pass1_nom & pass2_nom
        both_nom_concordant = both_nom & (np.sign(r1) == np.sign(r2))
        p_nom_1 = np.mean(pass1_nom)
        p_nom_2 = np.mean(pass2_nom)
        binom_p_nom_concord = float(stats.binomtest(int(np.sum(both_nom_concordant)), n=n_shared_active, p=max(1e-9, 0.5 * p_nom_1 * p_nom_2), alternative="greater").pvalue)

        # 3. Genome-wide correlation between r1 and r2
        gw_r, gw_p = stats.pearsonr(r1, r2)
        gw_sign_concord = float(np.mean(np.sign(r1) == np.sign(r2)) * 100.0)

        # Top replicating genes (sorted by min(|r1|, |r2|) among concordant nominal p<0.05)
        concord_indices = np.where(both_nom_concordant)[0]
        concord_list = []
        for ci in concord_indices:
            concord_list.append({
                "ensembl_id": str(ens_sub[ci]),
                "symbol": str(syms[ci]),
                "r_cohort1": round(float(r1[ci]), 4),
                "p_cohort1": round(float(p1[ci]), 5),
                "r_cohort2": round(float(r2[ci]), 4),
                "p_cohort2": round(float(p2[ci]), 5),
                "exceeds_both_emp95": bool(both_emp_concordant[ci]),
                "min_abs_r": round(float(min(abs(r1[ci]), abs(r2[ci]))), 4),
            })
        concord_list.sort(key=lambda x: x["min_abs_r"], reverse=True)

        # 4. Check the 100 genes in models/cell_type_genes.json
        table_eval = []
        if table_genes_list is not None:
            sym_to_shared_idx = {str(s): idx for idx, s in enumerate(shared_syms)}
            ens_to_shared_idx = {str(e): idx for idx, e in enumerate(shared_ens)}
            for g_entry in table_genes_list:
                g_ens = g_entry.get("gene", "")
                g_sym = g_entry.get("gene_symbol", g_ens)
                r_json = float(g_entry.get("correlation", 0.0))
                s_idx = ens_to_shared_idx.get(g_ens, sym_to_shared_idx.get(g_sym))
                if s_idx is not None:
                    li = lit_shared_i[s_idx]
                    pi = peri_shared_i[s_idx]
                    rl = float(r1_dict["r_pearson"][li])
                    pl = float(r1_dict["p_vals"][li])
                    rp = float(r2_dict["r_pearson"][pi])
                    pp = float(r2_dict["p_vals"][pi])
                    same_sign_c1_c2 = (np.sign(rl) == np.sign(rp)) and (rp != 0)
                    same_sign_json_c2 = (np.sign(r_json) == np.sign(rp)) and (rp != 0)
                    rep_nom = bool(pl < 0.05 and pp < 0.05 and same_sign_c1_c2)
                    rep_peri_nom = bool(pp < 0.05 and same_sign_json_c2)
                    rep_emp95 = bool(abs(rl) > thr1_emp95 and abs(rp) > thr2_emp95 and same_sign_c1_c2)
                    rep_peri_emp95 = bool(abs(rp) > thr2_emp95 and same_sign_json_c2)
                    table_eval.append({
                        "symbol": g_sym,
                        "ensembl_id": g_ens,
                        "r_json": round(r_json, 4),
                        "r_lit_donor": round(rl, 4),
                        "p_lit_donor": round(pl, 5),
                        "r_peri_donor": round(rp, 4),
                        "p_peri_donor": round(pp, 5),
                        "same_sign": bool(same_sign_json_c2),
                        "replicates_peri_p005_same_sign": rep_peri_nom,
                        "replicates_both_p005_same_sign": rep_nom,
                        "replicates_peri_emp95_same_sign": rep_peri_emp95,
                        "replicates_both_emp95_same_sign": rep_emp95,
                    })

        table_summary = {}
        if table_eval:
            df_t = pd.DataFrame(table_eval)
            tr_r, tr_p = stats.pearsonr(df_t["r_lit_donor"], df_t["r_peri_donor"])
            table_summary = {
                "n_table_evaluated": len(df_t),
                "same_sign_in_periheart_count": int(df_t["same_sign"].sum()),
                "replicates_peri_p005_same_sign_count": int(df_t["replicates_peri_p005_same_sign"].sum()),
                "replicates_both_p005_same_sign_count": int(df_t["replicates_both_p005_same_sign"].sum()),
                "replicates_peri_emp95_same_sign_count": int(df_t["replicates_peri_emp95_same_sign"].sum()),
                "replicates_both_emp95_same_sign_count": int(df_t["replicates_both_emp95_same_sign"].sum()),
                "r_correlation_across_100_table_genes": round(float(tr_r), 4),
                "p_correlation_across_100_table_genes": round(float(tr_p), 5),
                "replicating_genes_peri_p005": df_t[df_t["replicates_peri_p005_same_sign"]]["symbol"].tolist(),
                "replicating_genes_both_emp95": df_t[df_t["replicates_both_emp95_same_sign"]]["symbol"].tolist(),
            }
            df_t.to_csv(f"scratch/phaseE_table100_{name}.csv", index=False)

        summary = {
            "comparison_name": name,
            "n_shared_active_genes": n_shared_active,
            "thr1_emp95": thr1_emp95,
            "thr2_emp95": thr2_emp95,
            "pass1_emp95_count": int(np.sum(pass1_emp)),
            "pass2_emp95_count": int(np.sum(pass2_emp)),
            "both_emp95_any_sign_count": int(np.sum(both_emp)),
            "both_emp95_concordant_count": int(np.sum(both_emp_concordant)),
            "expected_emp95_overlap_any_sign": round(float(expected_overlap_emp), 2),
            "expected_emp95_overlap_concordant": round(float(0.5 * expected_overlap_emp), 2),
            "binom_p_emp95_any_sign": binom_p_emp,
            "binom_p_emp95_concordant": binom_p_emp_concord,
            "pass1_nom_p005_count": int(np.sum(pass1_nom)),
            "pass2_nom_p005_count": int(np.sum(pass2_nom)),
            "both_nom_p005_any_sign_count": int(np.sum(both_nom)),
            "both_nom_p005_concordant_count": int(np.sum(both_nom_concordant)),
            "expected_nom_concordant": round(float(0.5 * n_shared_active * p_nom_1 * p_nom_2), 2),
            "binom_p_nom_concordant": binom_p_nom_concord,
            "genome_wide_r_between_cohorts": round(float(gw_r), 4),
            "genome_wide_p_between_cohorts": float(gw_p),
            "genome_wide_sign_concordance_pct": round(gw_sign_concord, 2),
            "top_concordant_genes": concord_list[:30],
            "table_100_summary": table_summary,
        }
        print(f"\n--- INTERSECTION: {name} ({n_shared_active} shared active genes) ---")
        print(f"  Empirical 95th Null Overlap (Concordant): {summary['both_emp95_concordant_count']} "
              f"(Expected: {summary['expected_emp95_overlap_concordant']}, Binomial p={binom_p_emp_concord:.4e})")
        print(f"  Nominal p<0.05 Overlap (Concordant):      {summary['both_nom_p005_concordant_count']} "
              f"(Expected: {summary['expected_nom_concordant']}, Binomial p={binom_p_nom_concord:.4e})")
        print(f"  Genome-Wide r(Cohort1, Cohort2):          r={gw_r:+.4f} (p={gw_p:.4e}), Sign Concordance={gw_sign_concord:.1f}%")
        if table_summary:
            print(f"  Table 100 Genes -> Same Sign in PERIHEART: {table_summary['same_sign_in_periheart_count']}/100 | "
                  f"PERIHEART p<0.05 (same sign): {table_summary['replicates_peri_p005_same_sign_count']}/100 | "
                  f"Both Emp95 (same sign): {table_summary['replicates_both_emp95_same_sign_count']}/100")
            print(f"  Replicating Table Genes (PERIHEART p<0.05, same sign): {table_summary['replicating_genes_peri_p005']}")
        return summary

    with open(TABLE_PATH, "r") as f:
        ct_table = json.load(f)["cell_types"]
    vcm_100 = ct_table["regular_ventricular_cardiac_myocyte"]["pro_rejuvenation_genes"] + ct_table["regular_ventricular_cardiac_myocyte"]["aging_marker_genes"]
    fib_100 = ct_table["fibroblast"]["pro_rejuvenation_genes"] + ct_table["fibroblast"]["aging_marker_genes"]
    acm_100 = ct_table["regular_atrial_cardiac_myocyte"]["pro_rejuvenation_genes"] + ct_table["regular_atrial_cardiac_myocyte"]["aging_marker_genes"]

    inter_fib = analyze_intersection("Fibroblast_Lit14_vs_Peri54", res_lit_fib, res_peri_fib, fib_100)
    inter_vcm_to_cm = analyze_intersection("vCM_Lit14_vs_AtrialCM_Peri54", res_lit_vcm, res_peri_cm, vcm_100)
    inter_acm_to_cm = analyze_intersection("AtrialCM_Lit12_vs_AtrialCM_Peri54", res_lit_acm, res_peri_cm, acm_100)

    # E.4 Secondary Batch-Aware Pooled Sensitivity Analysis (68 donors with explicit cohort + center covariates)
    def run_pooled_ols_sensitivity(r1_dict, r2_dict, table_genes_list):
        d1 = r1_dict["donors"]
        d2 = r2_dict["donors"]
        ages_all = np.concatenate([r1_dict["ages"], r2_dict["ages"]])
        youth_all = -ages_all
        is_peri = np.array([0.0] * len(d1) + [1.0] * len(d2))
        is_sanger = np.array([1.0 if d.startswith("D") else 0.0 for d in d1] + [0.0] * len(d2))
        # Design matrix X: [1, youth_all, is_peri, is_sanger]
        X_des = np.column_stack([np.ones(len(ages_all)), youth_all, is_peri, is_sanger])
        XtX_inv = np.linalg.inv(X_des.T @ X_des)
        df_ols = len(ages_all) - X_des.shape[1]

        sym_to_shared_idx = {str(s): idx for idx, s in enumerate(shared_syms)}
        ens_to_shared_idx = {str(e): idx for idx, e in enumerate(shared_ens)}

        sig_p005 = 0
        sig_same_sign = 0
        for g_entry in table_genes_list:
            g_ens = g_entry.get("gene", "")
            g_sym = g_entry.get("gene_symbol", g_ens)
            r_json = float(g_entry.get("correlation", 0.0))
            s_idx = ens_to_shared_idx.get(g_ens, sym_to_shared_idx.get(g_sym))
            if s_idx is not None:
                y1 = r1_dict["mat"][:, lit_shared_i[s_idx]]
                y2 = r2_dict["mat"][:, peri_shared_i[s_idx]]
                y_all = np.concatenate([y1, y2])
                beta = XtX_inv @ (X_des.T @ y_all)
                resid = y_all - X_des @ beta
                s2 = float(np.sum(resid ** 2) / df_ols)
                se_beta1 = np.sqrt(max(1e-15, s2 * XtX_inv[1, 1]))
                t_val = beta[1] / se_beta1
                p_val = float(2.0 * stats.t.sf(abs(t_val), df=df_ols))
                if p_val < 0.05:
                    sig_p005 += 1
                    if np.sign(beta[1]) == np.sign(r_json):
                        sig_same_sign += 1
        return {"n_donors_pooled": len(ages_all), "df": df_ols, "table100_ols_p005": sig_p005, "table100_ols_p005_same_sign": sig_same_sign}

    ols_fib = run_pooled_ols_sensitivity(res_lit_fib, res_peri_fib, fib_100)
    ols_vcm = run_pooled_ols_sensitivity(res_lit_vcm, res_peri_cm, vcm_100)
    ols_acm = run_pooled_ols_sensitivity(res_lit_acm, res_peri_cm, acm_100)

    out_payload = {
        "null_summaries": {
            "litvinukova_vcm_14": res_lit_vcm["null_summary"],
            "litvinukova_acm_12": res_lit_acm["null_summary"],
            "litvinukova_fib_14": res_lit_fib["null_summary"],
            "periheart_cm_54": res_peri_cm["null_summary"],
            "periheart_fib_54": res_peri_fib["null_summary"],
        },
        "intersections": {
            "fibroblast": inter_fib,
            "vcm_to_atrial_cm": inter_vcm_to_cm,
            "atrial_cm_to_atrial_cm": inter_acm_to_cm,
        },
        "pooled_ols_sensitivity": {
            "fibroblast_68_donors": ols_fib,
            "vcm_to_cm_68_donors": ols_vcm,
            "acm_to_cm_66_donors": ols_acm,
        }
    }
    with open("scratch/phaseE_replication_summary.json", "w") as f:
        json.dump(out_payload, f, indent=2)
    print("\nSaved complete Phase E replication output to scratch/phaseE_replication_summary.json")


if __name__ == "__main__":
    main()
