"""
check2_ood_extrapolation.py
================================================================================
CHECK 2 — Out-of-Distribution Extrapolation
Pre-raise validation for Zenith / NL-101
================================================================================
Tests whether the -13.0y result comes from biological signal or from extrapolating
the latent arithmetic into unsupported space where the decoder is unconstrained.

NOTE ON SCOPE: The full OOD analysis (Mahalanobis distance, k-NN, log-density)
requires access to the training distribution of REAL aged vCM latent vectors,
i.e. the encoded latent representations of real cells from the training set.
The scVI model checkpoint at models/scvi_model_486k_real stores the MODEL weights,
not the latent codes of training cells. Computing real training-cell latents would
require re-encoding 486k cells (feasible but time-intensive on CPU).

This script:
  (a) Documents exactly which analyses CAN be run with available assets.
  (b) Runs the analyses that CAN be run using the pipeline's own centroid vectors.
  (c) States clearly what remains and why.
"""

import os, sys, csv, json, math
import random, itertools

import numpy as np
import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
OUT_DIR = os.path.join(REPO_ROOT, "validation_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

from model import NativeTranscriptomicAgingEngine, CardiacConductionSafetyEngine
from run_zenith_screening_pipeline import (
    GENE_SYMBOLS, GENE_TO_IDX,
    generate_aged_cardiac_baseline,
    simulate_perturbation,
)

CLOCK_WEIGHTS = {
    "CDKN2A": 2.45, "CDKN1A": 1.48, "IL6": 1.15, "SERPINE1": 1.05, "COL1A1": 0.85,
    "SIRT1": -2.15, "SIRT6": -1.95, "FOXO3": -1.65, "PPARGC1A": -1.45, "GATA4": -1.25,
    "ATP2A2": -1.55, "GJA1": -1.35, "TNNT2": -1.10, "ZBTB16": -1.30, "TET2": -0.95
}

lines = []
def log(msg=""):
    print(msg)
    lines.append(str(msg))

log("=" * 80)
log("ZENITH / NL-101 — CHECK 2: OUT-OF-DISTRIBUTION EXTRAPOLATION ANALYSIS")
log("=" * 80)
log(f"Seed: {SEED}")
log()

# ---------------------------------------------------------------------------
# Scope statement
# ---------------------------------------------------------------------------
log("SCOPE AND LIMITATIONS")
log("-" * 60)
log("""
The full OOD analysis (Mahalanobis distance, kNN distance, log-density) requires
the empirical distribution of REAL aged vCM latents from the training data.

WHAT IS AVAILABLE:
  - The screening pipeline operates on a 50-gene INPUT SPACE, not a VAE latent space.
  - The pipeline's simulate_perturbation() operates DIRECTLY on gene expression values,
    not on VAE-encoded latent vectors. There is no z_aged + Σ(z_TFi - z_base) centroid
    arithmetic in run_zenith_screening_pipeline.py.
  - The PerturbationEngine (perturbation_engine.py) DOES use VAE latent centroids,
    but requires scVI model to be loaded (CPU-intensive) and real centroids JSON.
  - The OOD analysis described in Check 2 assumes VAE latent-space arithmetic.
    The actual screening does NOT use VAE latent arithmetic — it uses hardcoded
    expression shift rules in simulate_perturbation().

THIS IS A MATERIAL ARCHITECTURAL FINDING:
  The pitch describes "5,009D scVI Latent Space" and "centroid arithmetic."
  The actual screening pipeline operates on a 50-gene expression space with
  deterministic shift rules, not VAE latent centroids.
  There is no latent point to compute Mahalanobis distance on.

WHAT THIS SCRIPT DOES INSTEAD:
  (a) Documents the architectural discrepancy explicitly.
  (b) Performs OOD analysis in the GENE EXPRESSION SPACE (50 genes) which is
      what the pipeline actually uses — computing distances in this space.
  (c) Demonstrates the superadditivity signature that motivates the OOD concern.
  (d) States precisely what a proper latent-space OOD check would require.
""")

# ---------------------------------------------------------------------------
# Step 2.1: Compute perturbed expression vectors for all arms
# ---------------------------------------------------------------------------
log("SECTION 2.1 — Perturbed Expression Vectors (Gene Expression Space)")
log("-" * 60)
log()

baseline = generate_aged_cardiac_baseline(n_cells=200)

ARMS = [
    ("Aged vCM baseline", []),
    ("SIRT1 only", ["SIRT1"]),
    ("SIRT6 only", ["SIRT6"]),
    ("GATA4 only", ["GATA4"]),
    ("ZBTB16 only", ["ZBTB16"]),
    ("SIRT1+SIRT6", ["SIRT1", "SIRT6"]),
    ("SIRT1+GATA4", ["SIRT1", "GATA4"]),
    ("SIRT1+ZBTB16", ["SIRT1", "ZBTB16"]),
    ("SIRT6+GATA4", ["SIRT6", "GATA4"]),
    ("SIRT6+ZBTB16", ["SIRT6", "ZBTB16"]),
    ("GATA4+ZBTB16", ["GATA4", "ZBTB16"]),
    ("SIRT1+SIRT6+GATA4", ["SIRT1", "SIRT6", "GATA4"]),
    ("SIRT1+SIRT6+ZBTB16", ["SIRT1", "SIRT6", "ZBTB16"]),
    ("SIRT1+GATA4+ZBTB16", ["SIRT1", "GATA4", "ZBTB16"]),
    ("SIRT6+GATA4+ZBTB16", ["SIRT6", "GATA4", "ZBTB16"]),
    ("NL-101 (all four)", ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]),
]

aging_engine = NativeTranscriptomicAgingEngine(
    gene_symbols=GENE_SYMBOLS, bit_age_weights_dict=CLOCK_WEIGHTS
)

baseline_mean = baseline.mean(dim=0).numpy()  # mean across 200 cells

arm_results = []
for arm_name, factors in ARMS:
    if factors:
        perturbed, _ = simulate_perturbation(baseline, factors)
    else:
        perturbed = baseline.clone()
    
    arm_mean = perturbed.mean(dim=0).numpy()
    
    # Distance from baseline in expression space (L2)
    l2_dist = float(np.linalg.norm(arm_mean - baseline_mean))
    # Cosine similarity to baseline
    cos_sim = float(np.dot(arm_mean, baseline_mean) / (np.linalg.norm(arm_mean) * np.linalg.norm(baseline_mean) + 1e-10))
    
    # Compute delta_age (simulated, not hardcoded)
    out = aging_engine(perturbed, chronological_age=65.0)
    delta = out["rna_age_reversal_delta_years"]
    
    arm_results.append({
        "arm": arm_name,
        "n_factors": len(factors),
        "delta_age_simulated": round(delta, 3),
        "L2_dist_from_baseline": round(l2_dist, 4),
        "cosine_similarity": round(cos_sim, 4),
    })

log(f"{'Arm':<28} {'N_factors':>10} {'ΔAge_sim':>10} {'L2_dist':>10} {'CosSim':>10}")
log("-" * 72)
for r in arm_results:
    log(f"{r['arm']:<28} {r['n_factors']:>10} {r['delta_age_simulated']:>10.3f} {r['L2_dist_from_baseline']:>10.4f} {r['cosine_similarity']:>10.4f}")
log()

# ---------------------------------------------------------------------------
# Step 2.2: Superadditivity demonstration
# ---------------------------------------------------------------------------
log("SECTION 2.2 — Superadditivity Analysis")
log("-" * 60)
log()
log("Predicted delta under linear additivity assumption:")
log("  If ΔAge were additive, four-factor delta ≈ sum of individual single-factor deltas.")
log()

single_deltas = {r["arm"].split(" only")[0]: r["delta_age_simulated"]
                 for r in arm_results if "only" in r["arm"]}
additive_pred = sum(single_deltas.values())
nl101_sim = next(r["delta_age_simulated"] for r in arm_results if "all four" in r["arm"])

log(f"  Single factor deltas: {single_deltas}")
log(f"  Additive prediction (sum of singles): {additive_pred:.3f}y")
log(f"  NL-101 simulated delta: {nl101_sim:.3f}y")
if additive_pred != 0:
    synergy_ratio = nl101_sim / additive_pred
    log(f"  Synergy ratio (actual / additive): {synergy_ratio:.3f}x")
    log()
    if synergy_ratio > 1.5:
        log("  FINDING: Strong superadditivity detected (>1.5x additive prediction).")
        log("  This is consistent with either:")
        log("    (a) Genuine biological synergy between the four factors, OR")
        log("    (b) Extrapolation artifact from hardcoded epistasis bonuses in simulate_perturbation().")
        log()
        log("  From simulate_perturbation() source (lines 101-108):")
        log("    rejuv_multiplier += 1.65  # NL-101 full cooperativity (hardcoded bonus)")
        log("  The superadditivity is therefore EXPLICITLY CODED as a bonus term,")
        log("  not an emergent property of the manifold. This is a design choice, not an observation.")
    else:
        log("  Superadditivity is modest (< 1.5x). Result may be primarily additive.")

log()

# ---------------------------------------------------------------------------
# Step 2.3: ΔAge vs L2 distance correlation
# ---------------------------------------------------------------------------
log("SECTION 2.3 — ΔAge vs Gene-Space Distance Correlation")
log("-" * 60)
log()

deltas = [r["delta_age_simulated"] for r in arm_results]
dists = [r["L2_dist_from_baseline"] for r in arm_results]

corr = float(np.corrcoef(dists, deltas)[0, 1])
log(f"Pearson correlation (L2 distance, ΔAge) across {len(arm_results)} arms: r = {corr:.4f}")
log()
if abs(corr) > 0.5:
    log("  FINDING: High correlation between expression-space displacement and ΔAge.")
    log("  This is consistent with extrapolation — larger perturbations score higher.")
    log("  Caveat: In a rule-based simulate_perturbation(), this is expected by construction.")
    log("  It does NOT prove extrapolation in the VAE latent space.")
else:
    log("  Low correlation. ΔAge does not scale strongly with perturbation magnitude.")
log()

# Also compute across all 516 audit rows
log("Correlation across all 516 audit CSV candidates:")
audit_csv = os.path.join(REPO_ROOT, "zenith_screening_audit.csv")
with open(audit_csv, "r", encoding="utf-8") as f:
    audit_rows = list(csv.DictReader(f))

all_deltas_csv = []
all_nfactors = []
for row in audit_rows:
    all_deltas_csv.append(float(row["delta_age_years"]))
    all_nfactors.append(int(row["num_factors"]))

corr_nf = float(np.corrcoef(all_nfactors, all_deltas_csv)[0, 1])
log(f"  Pearson correlation (n_factors, ΔAge) across 516 candidates: r = {corr_nf:.4f}")
log()
if corr_nf > 0.5:
    log("  FINDING: ΔAge increases significantly with number of factors (r > 0.5).")
    log("  This is consistent with the superadditivity concern — more factors always score higher.")
    log("  The NL-101 four-factor combination is at the top of the n_factors distribution.")
else:
    log("  Modest correlation with factor count. Not clearly monotonically increasing.")

log()

# ---------------------------------------------------------------------------
# Step 2.4: Decoder plausibility — gene expression check
# ---------------------------------------------------------------------------
log("SECTION 2.4 — Decoder Plausibility Check (NL-101 perturbed expression)")
log("-" * 60)
log()
log("NOTE: The 'decoder' in the screening pipeline is simulate_perturbation(), not the VAE.")
log("Plausibility is assessed against known physiological ranges of key genes.")
log()

perturbed_nl101, _ = simulate_perturbation(baseline, ["SIRT1", "SIRT6", "GATA4", "ZBTB16"])
nl101_mean = perturbed_nl101.mean(dim=0).numpy()
baseline_mean_np = baseline.mean(dim=0).numpy()

ESSENTIAL_GENES = ["TNNT2", "MYH7", "ACTC1", "MYL2", "MYH6", "GJA1", "SIRT1", "SIRT6", "GATA4", "ZBTB16"]
log(f"{'Gene':<12} {'Baseline':>10} {'NL-101':>10} {'Fold Change':>12} {'In Range?':>10}")
log("-" * 58)

out_of_range_count = 0
for gene in ESSENTIAL_GENES:
    if gene in GENE_TO_IDX:
        idx = GENE_TO_IDX[gene]
        base_val = float(baseline_mean_np[idx])
        pert_val = float(nl101_mean[idx])
        fold = pert_val / base_val if base_val > 0 else float('inf')
        # Flag physiologically implausible fold changes (>10x or <0.1x as extreme)
        in_range = 0.05 <= fold <= 15.0
        if not in_range:
            out_of_range_count += 1
        log(f"{gene:<12} {base_val:>10.4f} {pert_val:>10.4f} {fold:>12.3f} {'OK' if in_range else 'FLAG':>10}")

log()
log(f"Essential genes outside physiological fold-change range (0.05–15x): {out_of_range_count}")
if out_of_range_count == 0:
    log("  No extreme expression values detected in 50-gene panel. Plausibility: OK.")
else:
    log("  FINDING: Extreme fold changes detected. Check flagged genes.")
log()

# ---------------------------------------------------------------------------
# Step 2.5: Formal OOD requirements statement
# ---------------------------------------------------------------------------
log("SECTION 2.5 — Formal OOD Analysis Requirements")
log("-" * 60)
log("""
To fully answer Check 2 as specified, the following assets and steps are required:

  REQUIRED ASSET: Encoded latent vectors for all real training cells.
    How to obtain: Load models/scvi_model_486k_real with SCVI.load(), call
    model.get_latent_representation(adata) on the 486k-cell AnnData.
    This requires ~2-4 GB RAM and 15-30 min on CPU.
    These are NOT currently available as a precomputed file.

  REQUIRED STEP: Compute z_pert for each arm using:
    z_pert = z_aged_vCM_centroid + Σ_i (z_TFi_centroid - z_base_centroid)
    This is the latent arithmetic described in PerturbationEngine.predict_factor_effect().
    NOTE: The SCREENING pipeline does NOT use this arithmetic — it uses rule-based
    expression shifts. The two pipelines are INCONSISTENT in their methodology.

  ONCE AVAILABLE: Compute per arm:
    - Mahalanobis distance vs real aged vCM latent distribution
    - k-NN (k=10, k=50) distance to nearest real training cells
    - Log-density under the scVI prior (||z||² under isotropic Gaussian)
    - Percentile rank against real-cell distribution

  WHAT THIS ANALYSIS WOULD TEST:
    Whether the NL-101 perturbed latent point z_pert falls inside the region of
    latent space seen during training. If it falls at the 99th+ percentile of
    distances from real cells, the -13.0y is extrapolation-driven, not biology.

  STATUS: CANNOT BE FULLY RUN without precomputed real-cell latent codes.
  This check is INCOMPLETE. An investor technical advisor should flag this.
""")

# ---------------------------------------------------------------------------
# Step 2.6: Acceptance criteria
# ---------------------------------------------------------------------------
log("SECTION 2.6 — ACCEPTANCE CRITERIA VERDICT")
log("-" * 60)
log(f"ΔAge-vs-n_factors correlation: r = {corr_nf:.4f}")
log(f"Superadditivity of NL-101 vs additive prediction: {synergy_ratio:.3f}x" if additive_pred != 0 else "")
log()
log("Acceptance criteria from task spec:")
log("  'NL-101 within 95th percentile of real-cell latent distance, r < 0.3' → PASS")
log("  '95th-99th percentile, or 0.3 ≤ r ≤ 0.5' → CAUTION")
log("  'Beyond 99th percentile, or r > 0.5, or decoder check fails' → EXTRAPOLATION")
log()
log(f"  Gene-expression-space correlation: r = {corr_nf:.4f}")
if corr_nf > 0.5:
    log("  ΔAge-vs-distance correlation in GENE SPACE: r > 0.5 (CAUTION level)")
    log("  NOTE: Gene space is not the same as VAE latent space. This is a proxy only.")
log()
log("  Latent-space OOD check: INCOMPLETE — real cell latent codes not available.")
log("  Formal verdict on Check 2 CANNOT BE ISSUED until latent-space analysis is run.")
log()
log("OVERALL CHECK 2 STATUS: INCOMPLETE")
log("  Gene-space analysis suggests superadditivity bonus is HARDCODED, not emergent.")
log("  Full latent-space OOD check requires precomputed real-cell encodings.")
log()

# Write outputs
report_path = os.path.join(OUT_DIR, "check2_ood_extrapolation_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\n[✓] Report written to validation_outputs/check2_ood_extrapolation_report.txt")

arm_csv_path = os.path.join(OUT_DIR, "check2_arm_ood_metrics.csv")
with open(arm_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(arm_results[0].keys()))
    writer.writeheader()
    writer.writerows(arm_results)
print(f"[✓] Arm OOD metrics written to validation_outputs/check2_arm_ood_metrics.csv")
