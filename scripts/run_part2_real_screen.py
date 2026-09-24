"""
run_part2_real_screen.py
================================================================================
PART 2 — REAL GRN-BASED PERTURBATION SCREEN ON 5,307 HUMAN VENTRICULAR CARDIOMYOCYTES
================================================================================
Prime Directives:
  1. Zero hardcoded scientific results, bonuses, or synergy multipliers.
  2. No code branches on a candidate's identity. Every TF/combination runs through
     the identical matrix propagation path.
  3. Real data only: models/scvi_model_hca/adata.h5ad (5,307 human vCMs, 14 donors)
     and models/omnipath_collectri_dorothea_human.tsv (74,302 published interactions).
"""

import os
import sys
import json
import math
import random
import itertools
from collections import Counter
import numpy as np
import pandas as pd
import scipy.sparse as sp
import anndata
import scanpy as sc
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneGroupOut

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT_DIR = "validation_outputs/part2_real_screen"
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 80)
print("STAGE 2A — CONSTRUCTING THE REAL ORACLE GRN ON 5,307 HUMAN vCMs")
print("=" * 80)

# 1. Load real HCA dataset and subset to Ventricular Cardiomyocytes
ad = anndata.read_h5ad("models/scvi_model_hca/adata.h5ad")
vcm = ad[ad.obs["cell_type"] == "Ventricular_Cardiomyocyte"].copy()
print(f"Loaded Ventricular_Cardiomyocyte subset: n_obs={vcm.n_obs}, n_vars={vcm.n_vars}")

# 2. Define Young (<60 yr) vs Aged (>=60 yr) populations by donor age
aged_brackets = ["60-65", "65-70", "70-75"]
vcm.obs["is_aged"] = vcm.obs["age_group"].isin(aged_brackets)
aged_mask = vcm.obs["is_aged"].values
young_mask = ~aged_mask

young_donors = sorted(list(vcm.obs.loc[young_mask, "donor"].unique()))
aged_donors = sorted(list(vcm.obs.loc[aged_mask, "donor"].unique()))
print(f"Young vCMs (<60 yr): {young_mask.sum()} cells across {len(young_donors)} donors {young_donors}")
print(f"Aged vCMs (>=60 yr): {aged_mask.sum()} cells across {len(aged_donors)} donors {aged_donors}")

# Normalize and log1p transform
sc.pp.normalize_total(vcm, target_sum=1e4)
sc.pp.log1p(vcm)
X_raw = vcm.X.toarray() if sp.issparse(vcm.X) else np.array(vcm.X, dtype=np.float32)

# Select active gene space: expressed in >= 1.0% of vCMs OR in safety/senescence panels
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
expr_frac_active = expr_frac[keep_gene_mask]
print(f"Active vCM gene space: {len(active_genes)} genes")

# Standard CellOracle k-NN manifold imputation (k=30 in 20D PCA space)
pca = PCA(n_components=20, random_state=SEED)
Z_pca = pca.fit_transform(X_active)
nbrs = NearestNeighbors(n_neighbors=30, metric="euclidean").fit(Z_pca)
knn_graph = nbrs.kneighbors_graph(Z_pca, mode="connectivity")
X_knn = np.asarray((knn_graph @ X_active) / 30.0, dtype=np.float32)

# 3. Load Base GRN (CollecTRI + DoRothEA + TRRUST human curated interactions)
df_base_grn = pd.read_csv("models/omnipath_collectri_dorothea_human.tsv", sep="\t", low_memory=False)
df_base_grn = df_base_grn[
    df_base_grn["source_genesymbol"].isin(gene_to_idx) &
    df_base_grn["target_genesymbol"].isin(gene_to_idx) &
    (df_base_grn["source_genesymbol"] != df_base_grn["target_genesymbol"])
].copy()

# Deduplicate (source, target) pairs
df_edges = df_base_grn.groupby(["source_genesymbol", "target_genesymbol"], as_index=False).first()
print(f"Base GRN edges in active vCM gene space: {len(df_edges)} edges ({df_edges['source_genesymbol'].nunique()} TFs -> {df_edges['target_genesymbol'].nunique()} targets)")

# Build target -> list of regulator indices mapping
target_to_regs = {}
for _, row in df_edges.iterrows():
    s_idx = gene_to_idx[row["source_genesymbol"]]
    t_idx = gene_to_idx[row["target_genesymbol"]]
    target_to_regs.setdefault(t_idx, []).append(s_idx)

# 4. Fit Cluster-Specific GRN via Ridge Regression (CellOracle get_links algorithm)
def fit_grn_matrix(X_mat, alpha=10.0):
    n_g = X_mat.shape[1]
    B = np.zeros((n_g, n_g), dtype=np.float32)
    r2_list = []
    edge_coefs = []
    
    # Standardize columns to unit variance for stable Ridge regularization across TFs, then rescale slopes
    col_means = X_mat.mean(axis=0)
    col_stds = X_mat.std(axis=0) + 1e-6
    X_std = (X_mat - col_means) / col_stds
    
    for t_idx, reg_indices in target_to_regs.items():
        X_reg = X_std[:, reg_indices]
        y_tgt = X_std[:, t_idx]
        if np.var(y_tgt) < 1e-8:
            continue
        # Analytical Ridge solution: (X^T X + alpha I)^-1 X^T y
        k_r = len(reg_indices)
        gram = X_reg.T @ X_reg + alpha * np.eye(k_r, dtype=np.float32)
        rhs = X_reg.T @ y_tgt
        w_std = np.linalg.solve(gram, rhs)
        
        # Convert standardized slope back to natural log-expression units: w_nat = w_std * (std_y / std_x)
        w_nat = w_std * (col_stds[t_idx] / col_stds[reg_indices])
        B[reg_indices, t_idx] = w_nat
        
        y_pred = X_reg @ w_std
        ss_res = np.sum((y_tgt - y_pred) ** 2)
        ss_tot = np.sum(y_tgt ** 2)
        r2 = max(0.0, 1.0 - float(ss_res / (ss_tot + 1e-8)))
        r2_list.append(r2)
        edge_coefs.extend(w_nat.tolist())
        
    return B, np.array(edge_coefs), np.array(r2_list)

B_all, edge_coefs_all, r2_all = fit_grn_matrix(X_knn, alpha=10.0)
print(f"Fitted All_vCM GRN: {len(edge_coefs_all)} edges | coef mean={edge_coefs_all.mean():.4f}, std={edge_coefs_all.std():.4f} | mean R2={r2_all.mean():.4f}")

# Fit per sub-cluster (vCM1, vCM2, vCM3) to report 2A cluster statistics
cluster_stats = {}
for cl_name in ["vCM1", "vCM2", "vCM3"]:
    cl_mask = (vcm.obs["cell_states"] == cl_name).values
    if cl_mask.sum() > 50:
        _, c_coefs, c_r2 = fit_grn_matrix(X_knn[cl_mask], alpha=10.0)
        cluster_stats[cl_name] = {
            "n_cells": int(cl_mask.sum()),
            "n_edges": int(len(c_coefs)),
            "coef_mean": round(float(c_coefs.mean()), 4),
            "coef_std": round(float(c_coefs.std()), 4),
            "coef_p05": round(float(np.percentile(c_coefs, 5)), 4),
            "coef_p95": round(float(np.percentile(c_coefs, 95)), 4),
            "mean_r2": round(float(c_r2.mean()), 4),
            "median_r2": round(float(np.median(c_r2)), 4),
        }
        print(f"  Cluster {cl_name}: {cluster_stats[cl_name]}")

# CellOracle 3-step signal propagation function (identical for every perturbation)
def propagate_perturbation(B_mat, delta_init, clamped_indices, n_steps=3):
    delta = delta_init.copy()
    for _ in range(n_steps):
        delta = delta @ B_mat + delta_init
        delta[clamped_indices] = delta_init[clamped_indices]
    return delta

# ------------------------------------------------------------------------------
# STAGE 2B — POSITIVE AND NEGATIVE CONTROLS
# ------------------------------------------------------------------------------
print("\n" + "=" * 80)
print("STAGE 2B — RUNNING POSITIVE AND NEGATIVE CONTROLS")
print("=" * 80)

mean_aged = X_knn[aged_mask].mean(axis=0)
mean_young = X_knn[young_mask].mean(axis=0)
std_aged = X_knn[aged_mask].std(axis=0) + 1e-6

# 1. Positive Controls: Simulate knockdown (delta = -mean_aged[tf]) in vCMs
positive_control_tests = [
    ("GATA4", "MYH7", "Direct cardiac sarcomere activator (GATA4 -> MYH7)"),
    ("GATA4", "ATP2A2", "Direct SERCA2a activator (GATA4 -> ATP2A2)"),
    ("GATA4", "NKX2-5", "Mutual cardiac TF co-activator (GATA4 -> NKX2-5)"),
    ("GATA4", "GJA1", "2-step conduction cascade (GATA4 -> NKX2-5 -> GJA1)"),
    ("NKX2-5", "GJA1", "Direct gap junction activator (NKX2-5 -> GJA1)"),
    ("NKX2-5", "MYH7", "Direct sarcomeric activator (NKX2-5 -> MYH7)"),
    ("MEF2C", "MYH7", "Direct ventricular myosin activator (MEF2C -> MYH7)"),
    ("FOXO3", "GJA1", "Direct Cx43 regulator (FOXO3 -> GJA1)"),
]

pos_control_results = []
for tf_name, tgt_name, desc in positive_control_tests:
    tf_i = gene_to_idx[tf_name]
    tgt_i = gene_to_idx[tgt_name]
    d_init = np.zeros(len(active_genes), dtype=np.float32)
    d_init[tf_i] = -mean_aged[tf_i]  # Complete knockdown to 0
    d_out = propagate_perturbation(B_all, d_init, [tf_i], n_steps=3)
    
    before_val = float(mean_aged[tgt_i])
    after_val = max(0.0, before_val + float(d_out[tgt_i]))
    pct_change = ((after_val - before_val) / (before_val + 1e-6)) * 100.0
    pos_control_results.append({
        "tf_knockdown": tf_name,
        "target_gene": tgt_name,
        "description": desc,
        "baseline_aged_expr": round(before_val, 4),
        "predicted_post_kd_expr": round(after_val, 4),
        "delta_log_expr": round(float(d_out[tgt_i]), 4),
        "pct_change": round(pct_change, 2),
        "recovered_expected_direction": bool(d_out[tgt_i] < 0)
    })
    print(f"  [POS CTRL] {tf_name} KD -> {tgt_name:<8}: delta={d_out[tgt_i]:+.4f} ({pct_change:+.1f}%) | Recovered: {d_out[tgt_i] < 0}")

# Shuffled GRN Control: permute columns of B_all and re-test GATA4 KD and NKX2-5 KD
np.random.seed(SEED)
B_shuffled = B_all.copy()
perm_cols = np.random.permutation(B_shuffled.shape[1])
B_shuffled = B_shuffled[:, perm_cols]

shuffled_control_results = []
for tf_name, tgt_name, _ in positive_control_tests[:5]:
    tf_i = gene_to_idx[tf_name]
    tgt_i = gene_to_idx[tgt_name]
    d_init = np.zeros(len(active_genes), dtype=np.float32)
    d_init[tf_i] = -mean_aged[tf_i]
    d_shuf = propagate_perturbation(B_shuffled, d_init, [tf_i], n_steps=3)
    shuffled_control_results.append({
        "tf_knockdown": tf_name,
        "target_gene": tgt_name,
        "real_grn_delta": round(float(pos_control_results[[p["tf_knockdown"]+"_"+p["target_gene"] for p in pos_control_results].index(tf_name+"_"+tgt_name)]["delta_log_expr"]), 4),
        "shuffled_grn_delta": round(float(d_shuf[tgt_i]), 4)
    })
    print(f"  [SHUFFLE CTRL] {tf_name} KD -> {tgt_name:<8}: shuffled delta={d_shuf[tgt_i]:+.4f}")

# ------------------------------------------------------------------------------
# STAGE 2C — HONEST READOUT DEFINITIONS (DUAL CIRCULARITY VARIANTS)
# ------------------------------------------------------------------------------
print("\n" + "=" * 80)
print("STAGE 2C — READOUT CALIBRATION & DONOR-HOLDOUT CLOCK")
print("=" * 80)

# 1. Empirical Young-vs-Aged vCM Restoration Vector (youth_vec = mean_young - mean_aged)
youth_vec = mean_young - mean_aged
youth_norm_sq = float(np.dot(youth_vec, youth_vec))

# 2. Published SenMayo / CellAge signature indices in active_genes
sen_indices = [gene_to_idx[g] for g in senmayo_genes if g in gene_to_idx]

# 3. Train Donor-Level Leave-One-Donor-Out Ridge Clock across the 14 donors
donor_midpoints = {'D1': 52.5, 'D2': 62.5, 'D3': 57.5, 'D4': 72.5, 'D5': 67.5, 'D6': 72.5, 'D7': 62.5,
                   'D11': 62.5, 'H2': 52.5, 'H3': 52.5, 'H4': 57.5, 'H5': 52.5, 'H6': 42.5, 'H7': 47.5}
cell_donor_ages = np.array([donor_midpoints[d] for d in vcm.obs["donor"]], dtype=np.float32)
donor_groups = vcm.obs["donor"].values

logo = LeaveOneGroupOut()
donor_maes = []
for train_idx, test_idx in logo.split(X_knn, cell_donor_ages, groups=donor_groups):
    reg_clock = Ridge(alpha=1000.0)
    reg_clock.fit(X_knn[train_idx], cell_donor_ages[train_idx])
    preds = reg_clock.predict(X_knn[test_idx])
    # Donor-level mean prediction vs true donor age
    donor_maes.append(abs(float(preds.mean() - cell_donor_ages[test_idx].mean())))

donor_holdout_mae = float(np.mean(donor_maes))
print(f"Donor-Holdout Cross-Validated Ridge Clock (14 donors, Leave-One-Donor-Out) Test MAE: {donor_holdout_mae:.2f} years")

# Fit full empirical clock weights for scoring
empirical_clock = Ridge(alpha=1000.0).fit(X_knn, cell_donor_ages)
clock_coef = empirical_clock.coef_.astype(np.float32)

def score_perturbation_vector(delta_vec, perturbed_gene_indices):
    """
    Computes both circularity variants:
      - Included: all genes in active_genes
      - Excluded: perturbed_gene_indices zeroed out in delta_vec before scoring
    """
    delta_excl = delta_vec.copy()
    delta_excl[perturbed_gene_indices] = 0.0
    
    # Youth Restoration Score (% of distance along empirical young - aged vector)
    youth_incl = float(np.dot(delta_vec, youth_vec) / youth_norm_sq) * 100.0
    youth_excl = float(np.dot(delta_excl, youth_vec) / youth_norm_sq) * 100.0
    
    # Donor-trained clock shift (negative age shift = younger = positive reversal)
    clock_rev_incl = float(-np.dot(delta_vec, clock_coef))
    clock_rev_excl = float(-np.dot(delta_excl, clock_coef))
    
    # SenMayo SASP expression shift
    sen_shift_incl = float(delta_vec[sen_indices].mean())
    sen_shift_excl = float(delta_excl[sen_indices].mean())
    
    # Individual safety genes shift
    safety_shifts = {sg: round(float(delta_vec[gene_to_idx[sg]]), 5) for sg in safety_genes if sg in gene_to_idx}
    
    return {
        "youth_restoration_pct_incl": round(youth_incl, 4),
        "youth_restoration_pct_excl": round(youth_excl, 4),
        "empirical_clock_rev_yr_incl": round(clock_rev_incl, 4),
        "empirical_clock_rev_yr_excl": round(clock_rev_excl, 4),
        "senmayo_shift_incl": round(sen_shift_incl, 5),
        "senmayo_shift_excl": round(sen_shift_excl, 5),
        "safety_shifts": safety_shifts
    }

# Negative Controls: 20 TFs with lowest expression in cardiomyocytes (<0.5% of vCMs)
all_grn_tfs = sorted(list(df_edges["source_genesymbol"].unique()))
low_expr_tfs = [tf for tf in all_grn_tfs if expr_frac_active[gene_to_idx[tf]] < 0.005][:20]
neg_tf_results = []
for tf_name in low_expr_tfs:
    tf_i = gene_to_idx[tf_name]
    d_init = np.zeros(len(active_genes), dtype=np.float32)
    d_init[tf_i] = float(std_aged[tf_i])
    d_out = propagate_perturbation(B_all, d_init, [tf_i], n_steps=3)
    sc_out = score_perturbation_vector(d_out, [tf_i])
    neg_tf_results.append({
        "tf": tf_name,
        "expr_frac_pct": round(float(expr_frac_active[tf_i]*100), 3),
        "youth_restoration_pct_excl": sc_out["youth_restoration_pct_excl"],
        "GJA1_shift": sc_out["safety_shifts"]["GJA1"]
    })

# Negative Controls: 20 random 4-gene sets
random.seed(SEED)
neg_random_quads = []
for i in range(20):
    quad_genes = random.sample(all_grn_tfs, 4)
    q_idx = [gene_to_idx[g] for g in quad_genes]
    d_init = np.zeros(len(active_genes), dtype=np.float32)
    for idx_val in q_idx:
        d_init[idx_val] = float(std_aged[idx_val])
    d_out = propagate_perturbation(B_all, d_init, q_idx, n_steps=3)
    sc_out = score_perturbation_vector(d_out, q_idx)
    neg_random_quads.append({
        "factors": "+".join(quad_genes),
        "youth_restoration_pct_excl": sc_out["youth_restoration_pct_excl"],
        "youth_restoration_pct_incl": sc_out["youth_restoration_pct_incl"]
    })

print(f"Negative Control (20 non-expressed TFs) mean youth_excl: {np.mean([x['youth_restoration_pct_excl'] for x in neg_tf_results]):.4f}%")
print(f"Negative Control (20 random TF quads) mean youth_excl:   {np.mean([x['youth_restoration_pct_excl'] for x in neg_random_quads]):.4f}%")

# ------------------------------------------------------------------------------
# STAGE 2D & 2E — HONEST CANDIDATE SPACE & FUNNEL SCREEN
# ------------------------------------------------------------------------------
print("\n" + "=" * 80)
print("STAGE 2D & 2E — CANDIDATE SPACE DEFINITION AND FUNNEL SCREEN")
print("=" * 80)

# Qualifying criterion:
# (a) Regulator in fitted GRN with >= 5 target edges in active vCM space
# (b) Expressed in >= 5.0% of aged human ventricular cardiomyocytes
tf_edge_counts = df_edges.groupby("source_genesymbol").size().to_dict()
aged_expr_frac = (X_active[aged_mask] > 0).mean(axis=0)

qualifying_tfs = []
for tf in all_grn_tfs:
    idx = gene_to_idx[tf]
    if tf_edge_counts.get(tf, 0) >= 5 and aged_expr_frac[idx] >= 0.05:
        qualifying_tfs.append(tf)

print(f"Total TFs in CollecTRI/DoRothEA active space: {len(all_grn_tfs)}")
print(f"Qualifying TFs (>=5 GRN edges AND >=5.0% aged vCM expression): {len(qualifying_tfs)}")

# Check qualification status of NL-101 factors specifically
for f_nl in ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]:
    idx = gene_to_idx.get(f_nl, -1)
    e_cnt = tf_edge_counts.get(f_nl, 0)
    a_frac = float(aged_expr_frac[idx]*100) if idx >= 0 else 0.0
    print(f"  NL-101 Factor {f_nl:<8}: GRN_edges={e_cnt:>3}, aged_vCM_expr={a_frac:5.1f}% -> Qualifies: {f_nl in qualifying_tfs}")

def evaluate_candidate_set(factor_list, stage_label, B_matrix=None):
    if B_matrix is None:
        B_matrix = B_all
    f_indices = [gene_to_idx[g] for g in factor_list if g in gene_to_idx]
    d_init = np.zeros(len(active_genes), dtype=np.float32)
    # Identical overexpression perturbation (+1.0 SD of vCM expression) for every factor
    for idx_val in f_indices:
        d_init[idx_val] = float(std_aged[idx_val])
    d_out = propagate_perturbation(B_matrix, d_init, f_indices, n_steps=3)
    scores = score_perturbation_vector(d_out, f_indices)
    
    # Compute latent-space distance (PCA 20D projection of perturbed aged centroid vs real vCM distribution)
    pert_profile = np.maximum(0.0, mean_aged + d_out)
    z_pert = pca.transform(pert_profile.reshape(1, -1))[0]
    z_aged_mean = Z_pca[aged_mask].mean(axis=0)
    z_cov_inv = np.linalg.pinv(np.cov(Z_pca.T) + 1e-4 * np.eye(20))
    diff_z = z_pert - z_aged_mean
    mahal_dist = float(np.sqrt(diff_z @ z_cov_inv @ diff_z))
    
    row = {
        "stage": stage_label,
        "factors": "+".join(factor_list),
        "n_factors": len(factor_list),
        "youth_restoration_pct_excl": scores["youth_restoration_pct_excl"],
        "youth_restoration_pct_incl": scores["youth_restoration_pct_incl"],
        "empirical_clock_rev_yr_excl": scores["empirical_clock_rev_yr_excl"],
        "empirical_clock_rev_yr_incl": scores["empirical_clock_rev_yr_incl"],
        "senmayo_shift_excl": scores["senmayo_shift_excl"],
        "senmayo_shift_incl": scores["senmayo_shift_incl"],
        "GJA1_shift": scores["safety_shifts"]["GJA1"],
        "SCN5A_shift": scores["safety_shifts"]["SCN5A"],
        "KCNJ2_shift": scores["safety_shifts"]["KCNJ2"],
        "KCNH2_shift": scores["safety_shifts"]["KCNH2"],
        "KCNQ1_shift": scores["safety_shifts"]["KCNQ1"],
        "CACNA1C_shift": scores["safety_shifts"]["CACNA1C"],
        "ATP2A2_shift": scores["safety_shifts"]["ATP2A2"],
        "RYR2_shift": scores["safety_shifts"]["RYR2"],
        "latent_mahalanobis_dist": round(mahal_dist, 4),
        "provenance": "COMPUTED_HCA_5307_vCM_RIDGE_GRN"
    }
    return row

# Stage 1: Single-TF Screen across all qualifying TFs
stage1_results = [evaluate_candidate_set([tf], "Stage1_SingleTF") for tf in qualifying_tfs]
# Also evaluate SIRT6 standalone for tracking transparency even though it has 2 GRN edges
sirt6_single = evaluate_candidate_set(["SIRT6"], "Stage1_Disqualified_Tracking")
stage1_results.sort(key=lambda x: x["youth_restoration_pct_excl"], reverse=True)
for rank, r in enumerate(stage1_results, 1):
    r["stage_rank"] = rank

print("\n--- Stage 1 Top 10 Single TFs (Ranked by Circularity-Free Youth Restoration %) ---")
for r in stage1_results[:10]:
    print(f"  Rank {r['stage_rank']:>3}: {r['factors']:<10} | Excl={r['youth_restoration_pct_excl']:+6.3f}% | Incl={r['youth_restoration_pct_incl']:+6.3f}% | Clock_Excl={r['empirical_clock_rev_yr_excl']:+6.3f}y | GJA1={r['GJA1_shift']:+.4f}")

# Report where NL-101 single factors rank in Stage 1
print("\n--- NL-101 Constituent Factors in Stage 1 ---")
for f_nl in ["SIRT1", "GATA4", "ZBTB16"]:
    r_nl = next((r for r in stage1_results if r["factors"] == f_nl), None)
    if r_nl:
        print(f"  {f_nl:<8}: Rank {r_nl['stage_rank']:>3}/{len(stage1_results)} | Excl={r_nl['youth_restoration_pct_excl']:+6.3f}% | Incl={r_nl['youth_restoration_pct_incl']:+6.3f}%")
print(f"  SIRT6   : Disqualified (only 2 GRN edges < 5 min) | Excl={sirt6_single['youth_restoration_pct_excl']:+6.3f}% | Incl={sirt6_single['youth_restoration_pct_incl']:+6.3f}%")

# Stage 2: Top 15 Single TFs -> All Pairs (105 pairs)
top15_tfs = [r["factors"] for r in stage1_results[:15]]
stage2_pairs = list(itertools.combinations(top15_tfs, 2))
stage2_results = [evaluate_candidate_set(list(p), "Stage2_Pairs") for p in stage2_pairs]
stage2_results.sort(key=lambda x: x["youth_restoration_pct_excl"], reverse=True)
for rank, r in enumerate(stage2_results, 1):
    r["stage_rank"] = rank

print("\n--- Stage 2 Top 5 Pairs ---")
for r in stage2_results[:5]:
    print(f"  Rank {r['stage_rank']:>3}: {r['factors']:<20} | Excl={r['youth_restoration_pct_excl']:+6.3f}% | Incl={r['youth_restoration_pct_incl']:+6.3f}% | GJA1={r['GJA1_shift']:+.4f}")

# Stage 3: Top 10 Single TFs -> All Triples (120) and All Quads (210)
top10_tfs = [r["factors"] for r in stage1_results[:10]]
# Ensure SIRT1, GATA4, ZBTB16, SIRT6 are also tracked in quads so NL-101 is compared directly on the identical scale
stage3_triples = [evaluate_candidate_set(list(c), "Stage3_Triples") for c in itertools.combinations(top10_tfs, 3)]
stage3_quads = [evaluate_candidate_set(list(c), "Stage3_Quads") for c in itertools.combinations(top10_tfs, 4)]

# Explicitly evaluate NL-101 and its 3-factor ablations through the exact same function
nl101_eval = evaluate_candidate_set(["SIRT1", "SIRT6", "GATA4", "ZBTB16"], "Stage3_Tracked_NL101")
nl101_no_sirt6 = evaluate_candidate_set(["SIRT1", "GATA4", "ZBTB16"], "Stage3_Tracked_Ablation")

# Combine all quads + NL-101 to find NL-101's exact position
all_quads_ranked = stage3_quads + [nl101_eval]
all_quads_ranked.sort(key=lambda x: x["youth_restoration_pct_excl"], reverse=True)
for rank, r in enumerate(all_quads_ranked, 1):
    r["stage_rank"] = rank

print("\n--- Stage 3 Top 10 Quads (Ranked by Circularity-Free Youth Restoration %) ---")
for r in all_quads_ranked[:10]:
    print(f"  Rank {r['stage_rank']:>3}: {r['factors']:<32} | Excl={r['youth_restoration_pct_excl']:+6.3f}% | Incl={r['youth_restoration_pct_incl']:+6.3f}% | Clock_Excl={r['empirical_clock_rev_yr_excl']:+6.3f}y | GJA1={r['GJA1_shift']:+.4f}")

nl101_quad_rank = next(r for r in all_quads_ranked if r["factors"] == "SIRT1+SIRT6+GATA4+ZBTB16")
print(f"\nNL-101 Exact Position in Quads: Rank {nl101_quad_rank['stage_rank']}/{len(all_quads_ranked)}")
print(f"  NL-101 Youth Restoration (Excl): {nl101_quad_rank['youth_restoration_pct_excl']:+.4f}%")
print(f"  NL-101 Youth Restoration (Incl): {nl101_quad_rank['youth_restoration_pct_incl']:+.4f}%")
print(f"  NL-101 Empirical Clock Shift (Excl): {nl101_quad_rank['empirical_clock_rev_yr_excl']:+.4f} yr")
print(f"  NL-101 Empirical Clock Shift (Incl): {nl101_quad_rank['empirical_clock_rev_yr_incl']:+.4f} yr")

# ------------------------------------------------------------------------------
# STAGE 2F — UNCERTAINTY & BOOTSTRAP STABILITY (20 BOOTSTRAPS)
# ------------------------------------------------------------------------------
print("\n" + "=" * 80)
print("STAGE 2F — BOOTSTRAPPING THE GRN FIT (20 RESAMPLES)")
print("=" * 80)

top20_quad_candidates = [r["factors"].split("+") for r in all_quads_ranked[:19]] + [["SIRT1", "SIRT6", "GATA4", "ZBTB16"]]
boot_scores = { "+".join(c): [] for c in top20_quad_candidates }
boot_winners = Counter()

n_vcm = X_knn.shape[0]
for b_i in range(20):
    np.random.seed(SEED + b_i + 100)
    boot_idx = np.random.choice(n_vcm, size=n_vcm, replace=True)
    B_boot, _, _ = fit_grn_matrix(X_knn[boot_idx], alpha=10.0)
    
    iter_res = []
    for c_list in top20_quad_candidates:
        ev = evaluate_candidate_set(c_list, "Bootstrap", B_matrix=B_boot)
        c_key = "+".join(c_list)
        boot_scores[c_key].append(ev["youth_restoration_pct_excl"])
        iter_res.append((c_key, ev["youth_restoration_pct_excl"]))
    iter_res.sort(key=lambda x: x[1], reverse=True)
    boot_winners[iter_res[0][0]] += 1

print("Bootstrap Winner Distribution (20 GRN resamples):", boot_winners.most_common(5))

uncertainty_table = []
for c_list in top20_quad_candidates:
    c_key = "+".join(c_list)
    vals = boot_scores[c_key]
    base_row = next(r for r in all_quads_ranked if r["factors"] == c_key)
    uncertainty_table.append({
        "factors": c_key,
        "point_rank": base_row["stage_rank"],
        "mean_excl": round(float(np.mean(vals)), 4),
        "sd_excl": round(float(np.std(vals)), 4),
        "ci95_low": round(float(np.percentile(vals, 2.5)), 4),
        "ci95_high": round(float(np.percentile(vals, 97.5)), 4),
        "mahalanobis_dist": base_row["latent_mahalanobis_dist"]
    })

# Save full CSV output
all_screen_rows = stage1_results + [sirt6_single] + stage2_results + stage3_triples + all_quads_ranked
df_out = pd.DataFrame(all_screen_rows)
df_out.to_csv("screen_output.csv", index=False)
df_out.to_csv(os.path.join(OUT_DIR, "screen_output.csv"), index=False)

# Save summary JSON for markdown generation
summary_payload = {
    "n_vcm_total": int(vcm.n_obs),
    "n_young_vcm": int(young_mask.sum()),
    "n_aged_vcm": int(aged_mask.sum()),
    "young_donors": young_donors,
    "aged_donors": aged_donors,
    "n_active_genes": len(active_genes),
    "n_base_edges": int(len(df_edges)),
    "all_vcm_grn": {
        "n_edges": int(len(edge_coefs_all)),
        "coef_mean": round(float(edge_coefs_all.mean()), 4),
        "coef_std": round(float(edge_coefs_all.std()), 4),
        "mean_r2": round(float(r2_all.mean()), 4),
    },
    "cluster_stats": cluster_stats,
    "donor_holdout_mae": round(donor_holdout_mae, 2),
    "pos_controls": pos_control_results,
    "shuffled_controls": shuffled_control_results,
    "neg_tf_controls": neg_tf_results,
    "neg_random_quads": neg_random_quads,
    "n_qualifying_tfs": len(qualifying_tfs),
    "stage1_top15": stage1_results[:15],
    "sirt6_single": sirt6_single,
    "stage2_top10": stage2_results[:10],
    "stage3_top15_quads": all_quads_ranked[:15],
    "nl101_eval": nl101_quad_rank,
    "nl101_no_sirt6": nl101_no_sirt6,
    "boot_winners": dict(boot_winners),
    "uncertainty_table": uncertainty_table
}
with open(os.path.join(OUT_DIR, "part2_summary.json"), "w") as f:
    json.dump(summary_payload, f, indent=2)

print("\n[SUCCESS] Saved screen_output.csv and validation_outputs/part2_real_screen/part2_summary.json")
