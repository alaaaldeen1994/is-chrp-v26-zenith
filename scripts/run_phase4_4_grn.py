import os
import sys
import json
import math
import random
import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.stats as stats
import anndata
import scanpy as sc
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

sys.stdout.reconfigure(encoding="utf-8")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_DIR)

def main():
    print("=" * 75)
    print("PHASE 4.4: EXACT GRN NULL DISTRIBUTIONS & DEGREE ARTIFACT TEST")
    print("=" * 75)

    ad = anndata.read_h5ad("models/scvi_model_hca/adata.h5ad")
    vcm = ad[ad.obs["cell_type"] == "Ventricular_Cardiomyocyte"].copy()

    aged_brackets = ["60-65", "65-70", "70-75"]
    vcm.obs["is_aged"] = vcm.obs["age_group"].isin(aged_brackets)
    aged_mask = vcm.obs["is_aged"].values
    young_mask = ~aged_mask

    sc.pp.normalize_total(vcm, target_sum=1e4)
    sc.pp.log1p(vcm)
    X_raw = vcm.X.toarray() if sp.issparse(vcm.X) else np.array(vcm.X, dtype=np.float32)

    expr_frac = (X_raw > 0).mean(axis=0)
    safety_genes = ["GJA1", "SCN5A", "KCNJ2", "KCNH2", "KCNQ1", "CACNA1C", "ATP2A2", "RYR2"]
    senmayo_genes = [
        "CDKN1A", "CDKN2A", "SERPINE1", "IL6", "GDF15", "IGFBP7", "IGFBP3", "TIMP1", "TIMP2",
        "JUN", "FOS", "STAT3", "TP53", "CCL2", "CXCL8", "MMP2", "MMP9", "VEGFA", "ICAM1", "CTGF"
    ]
    tracked_factors = ["SIRT1", "SIRT6", "GATA4", "ZBTB16", "NKX2-5", "TBX5", "MEF2C", "FOXO3"]
    must_keep = set(safety_genes + senmayo_genes + tracked_factors)

    keep_gene_mask = (expr_frac >= 0.01) | np.array([g in must_keep for g in vcm.var_names])
    active_genes = list(vcm.var_names[keep_gene_mask])
    gene_to_idx = {g: i for i, g in enumerate(active_genes)}
    X_active = X_raw[:, keep_gene_mask]

    pca = PCA(n_components=20, random_state=SEED)
    Z_pca = pca.fit_transform(X_active)
    nbrs = NearestNeighbors(n_neighbors=30, metric="euclidean").fit(Z_pca)
    knn_graph = nbrs.kneighbors_graph(Z_pca, mode="connectivity")
    X_knn = np.asarray((knn_graph @ X_active) / 30.0, dtype=np.float32)

    df_base_grn = pd.read_csv("models/omnipath_collectri_dorothea_human.tsv", sep="\t", low_memory=False)
    df_base_grn = df_base_grn[
        df_base_grn["source_genesymbol"].isin(gene_to_idx) &
        df_base_grn["target_genesymbol"].isin(gene_to_idx) &
        (df_base_grn["source_genesymbol"] != df_base_grn["target_genesymbol"])
    ].copy()
    df_edges = df_base_grn.groupby(["source_genesymbol", "target_genesymbol"], as_index=False).first()

    target_to_regs = {}
    for _, row in df_edges.iterrows():
        s_idx = gene_to_idx[row["source_genesymbol"]]
        t_idx = gene_to_idx[row["target_genesymbol"]]
        target_to_regs.setdefault(t_idx, []).append(s_idx)

    n_g = X_knn.shape[1]
    B_all = np.zeros((n_g, n_g), dtype=np.float32)
    col_means = X_knn.mean(axis=0)
    col_stds = X_knn.std(axis=0) + 1e-6
    X_std = (X_knn - col_means) / col_stds
    alpha = 10.0
    for t_idx, reg_indices in target_to_regs.items():
        X_reg = X_std[:, reg_indices]
        y_tgt = X_std[:, t_idx]
        if np.var(y_tgt) < 1e-8:
            continue
        k_r = len(reg_indices)
        gram = X_reg.T @ X_reg + alpha * np.eye(k_r, dtype=np.float32)
        rhs = X_reg.T @ y_tgt
        w_std = np.linalg.solve(gram, rhs)
        w_nat = w_std * (col_stds[t_idx] / col_stds[reg_indices])
        B_all[reg_indices, t_idx] = w_nat

    mean_aged = X_knn[aged_mask].mean(axis=0)
    mean_young = X_knn[young_mask].mean(axis=0)
    std_aged = X_knn[aged_mask].std(axis=0) + 1e-6
    youth_vec = mean_young - mean_aged
    youth_norm_sq = float(np.dot(youth_vec, youth_vec))

    def eval_tfs(tf_names):
        q_idx = [gene_to_idx[g] for g in tf_names]
        d_init = np.zeros(n_g, dtype=np.float32)
        for idx_val in q_idx:
            d_init[idx_val] = float(std_aged[idx_val])
        delta = d_init.copy()
        for _ in range(3):
            delta = delta @ B_all + d_init
            delta[q_idx] = d_init[q_idx]
        delta_excl = delta.copy()
        delta_excl[q_idx] = 0.0
        youth_excl = float(np.dot(delta_excl, youth_vec) / (youth_norm_sq + 1e-8)) * 100.0
        return youth_excl

    # Compute out-degree per TF
    tf_out_deg = {}
    for g in active_genes:
        g_i = gene_to_idx[g]
        tf_out_deg[g] = int((np.abs(B_all[g_i, :]) > 0).sum())

    screen_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "quarantine", "track2", "screen_output.csv")
    if not os.path.exists(screen_csv):
        screen_csv = "screen_output.csv"
    df_screen = pd.read_csv(screen_csv)
    df_singles = df_screen[df_screen["stage"] == "Stage1_SingleTF"].copy()

    df_quads = df_screen[df_screen["stage"] == "Stage4_Quad"].copy()

    df_singles["n_active_edges"] = [tf_out_deg.get(f, 0) for f in df_singles["factors"]]
    df_quads["n_active_edges"] = [
        sum(tf_out_deg.get(t, 0) for t in f.split("+")) for f in df_quads["factors"]
    ]

    # (b) Degree correlation across all 239 single TFs
    deg_vec = df_singles["n_active_edges"].values.astype(float)
    score_vec = df_singles["youth_restoration_pct_excl"].values.astype(float)
    r_deg_p, p_deg_p = stats.pearsonr(deg_vec, score_vec)
    r_deg_s, p_deg_s = stats.spearmanr(deg_vec, score_vec)
    log_deg = np.log10(deg_vec + 1.0)
    r_logdeg_p, p_logdeg_p = stats.pearsonr(log_deg, score_vec)
    r2_logdeg = r_logdeg_p ** 2

    # Also check correlation between out-degree and |score| (magnitude) and among positive TFs
    r_abs_deg_p, p_abs_deg_p = stats.pearsonr(log_deg, np.abs(score_vec))
    pos_singles = df_singles[df_singles["youth_restoration_pct_excl"] > 0].copy()
    r_pos_deg_p, p_pos_deg_p = stats.pearsonr(
        np.log10(pos_singles["n_active_edges"].values + 1.0),
        pos_singles["youth_restoration_pct_excl"].values
    )

    slope_s, int_s, _, _, _ = stats.linregress(log_deg, score_vec)
    df_singles["expected_from_log_deg"] = int_s + slope_s * log_deg
    df_singles["degree_residual"] = score_vec - df_singles["expected_from_log_deg"]
    df_singles_res = df_singles.sort_values("degree_residual", ascending=False).reset_index(drop=True)

    print(f"[4.4b] Single-TF (n={len(df_singles)}) Out-Degree vs Score: Pearson r = {r_deg_p:+.4f} (p={p_deg_p:.4e}), Spearman rho = {r_deg_s:+.4f} (p={p_deg_s:.4e})")
    print(f"[4.4b] log10(Out-Degree) vs Score: Pearson r = {r_logdeg_p:+.4f} (R^2 = {r2_logdeg:.4f}, p={p_logdeg_p:.4e})")
    print(f"[4.4b] log10(Out-Degree) vs |Score| (magnitude): Pearson r = {r_abs_deg_p:+.4f} (R^2 = {r_abs_deg_p**2:.4f}, p={p_abs_deg_p:.4e})")
    print(f"[4.4b] Positive Single-TFs (n={len(pos_singles)}) log10(Out-Degree) vs Score: Pearson r = {r_pos_deg_p:+.4f} (R^2 = {r_pos_deg_p**2:.4f}, p={p_pos_deg_p:.4e})")
    print("       Top 5 Single-TFs by Degree-Adjusted Residual:")
    for i in range(5):
        r0 = df_singles_res.iloc[i]
        print(f"         #{i+1}: {r0['factors']:<8} | raw={r0['youth_restoration_pct_excl']:+.4f}% | edges={int(r0['n_active_edges']):<4} | residual={r0['degree_residual']:+.4f}%")

    # Verify winner exact score
    winner_tfs = ["NFKB1", "MITF", "CTCF", "HIF1A"]
    winner_score = eval_tfs(winner_tfs)
    winner_edges = sum(tf_out_deg[t] for t in winner_tfs)
    print(f"\nWinner {winner_tfs}: exact score = {winner_score:+.4f}% (table: +6.0690%), total edges = {winner_edges}")

    # (a) 1,000 Random 4-TF combinations from the 239 candidate TFs
    cand_tfs = df_singles["factors"].tolist()
    np.random.seed(42)
    rand_scores = []
    rand_edges = []
    for _ in range(1000):
        chosen = list(np.random.choice(cand_tfs, size=4, replace=False))
        rand_scores.append(eval_tfs(chosen))
        rand_edges.append(sum(tf_out_deg[t] for t in chosen))
    rand_scores = np.array(rand_scores)

    # 1,000 Degree-Matched 4-TF combinations (total edges within +/-15% of winner_edges, i.e. [636, 860])
    # To efficiently sample 4-TF combinations whose total out-degree matches ~748 (avg 187 edges/TF),
    # sample from candidate TFs with out-degree >= 60 (hub TFs)
    hub_pool = [t for t in cand_tfs if tf_out_deg[t] >= 60]
    deg_scores = []
    deg_edges = []
    seen_sets = {frozenset(winner_tfs)}
    attempts = 0
    while len(deg_scores) < 1000 and attempts < 100000:
        attempts += 1
        chosen = list(np.random.choice(hub_pool, size=4, replace=False))
        fset = frozenset(chosen)
        if fset in seen_sets:
            continue
        ed_sum = sum(tf_out_deg[t] for t in chosen)
        if int(winner_edges * 0.85) <= ed_sum <= int(winner_edges * 1.15):
            seen_sets.add(fset)
            deg_scores.append(eval_tfs(chosen))
            deg_edges.append(ed_sum)
    deg_scores = np.array(deg_scores)

    p_emp_rand = float((rand_scores >= winner_score).sum() / len(rand_scores))
    pct_rand = float((rand_scores < winner_score).mean() * 100.0)
    print(f"\n[4.4a] Random 4-TF Null (n=1000, mean edges={np.mean(rand_edges):.1f}):")
    print(f"       mean={rand_scores.mean():+.4f}%, SD={rand_scores.std():.4f}%, 5th={np.percentile(rand_scores, 5):+.4f}%, "
          f"50th={np.percentile(rand_scores, 50):+.4f}%, 95th={np.percentile(rand_scores, 95):+.4f}%, max={rand_scores.max():+.4f}%")
    print(f"       Positive (>0): {(rand_scores > 0).sum()}/1000 | Negative (<0): {(rand_scores < 0).sum()}/1000")
    print(f"       Winner (+6.069%) vs Random Null: percentile={pct_rand:.2f}%, empirical p={p_emp_rand:.4f}")

    p_emp_deg = float((deg_scores >= winner_score).sum() / len(deg_scores))
    pct_deg = float((deg_scores < winner_score).mean() * 100.0)
    print(f"\n[4.4a] Degree-Matched 4-TF Null (n={len(deg_scores)}, mean edges={np.mean(deg_edges):.1f}, range=[{min(deg_edges)}, {max(deg_edges)}]):")
    print(f"       mean={deg_scores.mean():+.4f}%, SD={deg_scores.std():.4f}%, 5th={np.percentile(deg_scores, 5):+.4f}%, "
          f"50th={np.percentile(deg_scores, 50):+.4f}%, 95th={np.percentile(deg_scores, 95):+.4f}%, max={deg_scores.max():+.4f}%")
    print(f"       Positive (>0): {(deg_scores > 0).sum()}/{len(deg_scores)} | Negative (<0): {(deg_scores < 0).sum()}/{len(deg_scores)}")
    print(f"       Winner (+6.069%) vs Degree-Matched Null: percentile={pct_deg:.2f}%, empirical p={p_emp_deg:.4f}")

    # Regress all 211 Stage-4 Quads on log10(n_active_edges) and check residual ranking!
    q_deg = df_quads["n_active_edges"].values.astype(float)
    q_log_deg = np.log10(q_deg + 1.0)
    q_scores = df_quads["youth_restoration_pct_excl"].values.astype(float)
    q_slope, q_int, q_r, q_p, _ = stats.linregress(q_log_deg, q_scores)
    df_quads["degree_residual"] = q_scores - (q_int + q_slope * q_log_deg)
    df_quads_res = df_quads.sort_values("degree_residual", ascending=False).reset_index(drop=True)
    winner_res_rank = int(df_quads_res[df_quads_res["factors"] == "NFKB1+MITF+CTCF+HIF1A"].index[0]) + 1

    print(f"\n[4.4b] Across 211 Evaluated Quads, log10(degree) vs Score: Pearson r = {q_r:+.4f} (R^2 = {q_r**2:.4f}, p={q_p:.4e})")
    print(f"       Winner NFKB1+MITF+CTCF+HIF1A rank after regressing out log10(degree): Rank #{winner_res_rank} / 211")
    print("       Top 5 Quads by Degree-Adjusted Residual:")
    for i in range(5):
        r0 = df_quads_res.iloc[i]
        print(f"         #{i+1}: {r0['factors']:<28} | raw={r0['youth_restoration_pct_excl']:+.4f}% | edges={int(r0['n_active_edges']):<4} | residual={r0['degree_residual']:+.4f}%")

    # (c) Spread across all 211 quads
    n_in_ci = int(((q_scores >= 5.765) & (q_scores <= 6.249)).sum())
    print(f"\n[4.4c] Quads inside winner's 95% bootstrap CI ([+5.765%, +6.249%]): {n_in_ci} / 211")
    print("       Top 10 Stage-4 Quads:")
    for i in range(10):
        r0 = df_quads.iloc[i]
        print(f"         #{i+1}: {r0['factors']:<28} | youth_excl={r0['youth_restoration_pct_excl']:+.4f}% | edges={int(r0['n_active_edges'])} | GJA1={r0['GJA1_shift']:+.5f}")

    out_json = {
        "single_tf": {
            "n_tfs": len(df_singles),
            "r_deg": float(r_deg_p), "p_deg": float(p_deg_p),
            "rho_deg": float(r_deg_s), "p_rho_deg": float(p_deg_s),
            "r_log_deg": float(r_logdeg_p), "r2_log_deg": float(r2_logdeg), "p_log_deg": float(p_logdeg_p),
            "r_abs_score_log_deg": float(r_abs_deg_p), "r2_abs_score_log_deg": float(r_abs_deg_p**2),
            "r_pos_tf_log_deg": float(r_pos_deg_p), "r2_pos_tf_log_deg": float(r_pos_deg_p**2),
        },
        "quads": {
            "n_quads": len(df_quads),
            "r_log_deg": float(q_r), "r2_log_deg": float(q_r**2), "p_log_deg": float(q_p),
            "winner_residual_rank": winner_res_rank,
            "n_in_winner_95ci": n_in_ci,
        },
        "random_null_1000": {
            "mean": float(rand_scores.mean()), "sd": float(rand_scores.std()),
            "p5": float(np.percentile(rand_scores, 5)), "p50": float(np.percentile(rand_scores, 50)),
            "p95": float(np.percentile(rand_scores, 95)), "max": float(rand_scores.max()),
            "n_pos": int((rand_scores > 0).sum()), "n_neg": int((rand_scores < 0).sum()),
            "winner_pct": pct_rand, "winner_p": p_emp_rand,
        },
        "degree_matched_null": {
            "n": int(len(deg_scores)),
            "mean_edges": float(np.mean(deg_edges)),
            "mean": float(deg_scores.mean()), "sd": float(deg_scores.std()),
            "p5": float(np.percentile(deg_scores, 5)), "p50": float(np.percentile(deg_scores, 50)),
            "p95": float(np.percentile(deg_scores, 95)), "max": float(deg_scores.max()),
            "n_pos": int((deg_scores > 0).sum()), "n_neg": int((deg_scores < 0).sum()),
            "winner_pct": pct_deg, "winner_p": p_emp_deg,
        }
    }
    with open("scratch/phase4_4_grn_summary.json", "w") as f:
        json.dump(out_json, f, indent=2)

if __name__ == "__main__":
    main()
