"""
check3_reproducibility.py
================================================================================
CHECK 3 — Reproducibility and Gate Stability
Pre-raise validation for Zenith / NL-101
================================================================================
Tests:
  3.1 Make pipeline deterministic (seed injection)
  3.2 Bitwise reproducibility (3 runs, same seed)
  3.3 Stability across 20 seeds
  3.4 Gate-margin analysis (ESI 0.928 ± 0.029 vs gate 0.90)

Rules:
 - No modifications to screening logic, gates, thresholds, model parameters.
 - Report failures prominently.
"""

import os, sys, csv, json, hashlib, random, copy
from collections import defaultdict

import numpy as np
import torch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
OUT_DIR = os.path.join(REPO_ROOT, "validation_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

from model import NativeTranscriptomicAgingEngine, CardiacConductionSafetyEngine, ThresholdSafetyGate
from run_zenith_screening_pipeline import GENE_SYMBOLS, GENE_TO_IDX, simulate_perturbation

CLOCK_WEIGHTS = {
    "CDKN2A": 2.45, "CDKN1A": 1.48, "IL6": 1.15, "SERPINE1": 1.05, "COL1A1": 0.85,
    "SIRT1": -2.15, "SIRT6": -1.95, "FOXO3": -1.65, "PPARGC1A": -1.45, "GATA4": -1.25,
    "ATP2A2": -1.55, "GJA1": -1.35, "TNNT2": -1.10, "ZBTB16": -1.30, "TET2": -0.95
}

NL101_FACTORS = ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]

CARD_POOL = ["SIRT1", "SIRT6", "GATA4", "ZBTB16", "FOXO3", "PPARGC1A",
             "MEF2C", "TBX5", "NKX2-5", "HAND2", "ESRRG", "TET2"]

import itertools

HARDCODED_NAMES = {
    "NL-101 (Zenith Lead)": {"delta": 13.00, "esi": 0.928},
    "Yamanaka OSKM (Control)": {"delta": 6.00, "esi": 0.240},
    "Sinclair OSK (Control)": {"delta": 7.00, "esi": 0.260},
    "Srivastava GMT (Control)": {"delta": 0.80, "esi": 0.960},
    "Dual Sirtuin (Benchmark)": {"delta": 5.40, "esi": 0.840},
    "Ablation: dSIRT1": {"delta": 8.10, "esi": 0.920},
    "Ablation: dSIRT6": {"delta": 6.90, "esi": 0.930},
    "Ablation: dGATA4": {"delta": 12.80, "esi": 0.680},
    "Ablation: dZBTB16": {"delta": 4.20, "esi": 0.938},
}

def seed_all(seed: int):
    """Seed all RNG sources for deterministic runs."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)

def run_screen_for_seed(seed: int, num_random: int = 500):
    """Run full combinatorial screen for a given seed. Returns list of result dicts."""
    seed_all(seed)
    
    aging_engine = NativeTranscriptomicAgingEngine(
        gene_symbols=GENE_SYMBOLS, bit_age_weights_dict=CLOCK_WEIGHTS
    )
    safety_engine = CardiacConductionSafetyEngine(gene_symbols=GENE_SYMBOLS)
    conformal_evaluator = ThresholdSafetyGate(alpha=0.01)
    
    # Generate aged baseline (seed-dependent due to randn)
    from run_zenith_screening_pipeline import generate_aged_cardiac_baseline
    baseline_counts = generate_aged_cardiac_baseline(n_cells=200)
    
    # Curated candidates
    curated_candidates = [
        ("NL-101 (Zenith Lead)", ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]),
        ("Yamanaka OSKM (Control)", ["POU5F1", "SOX2", "KLF4", "MYC"]),
        ("Sinclair OSK (Control)", ["POU5F1", "SOX2", "KLF4"]),
        ("Srivastava GMT (Control)", ["GATA4", "MEF2C", "TBX5"]),
        ("Dual Sirtuin (Benchmark)", ["SIRT1", "SIRT6"]),
        ("Ablation: dSIRT1", ["SIRT6", "GATA4", "ZBTB16"]),
        ("Ablation: dSIRT6", ["SIRT1", "GATA4", "ZBTB16"]),
        ("Ablation: dGATA4", ["SIRT1", "SIRT6", "ZBTB16"]),
        ("Ablation: dZBTB16", ["SIRT1", "SIRT6", "GATA4"]),
        ("Cardiac Triad 1", ["GATA4", "NKX2-5", "TBX5"]),
        ("Metabolic Sirtuin", ["SIRT1", "PPARGC1A", "ESRRG"]),
        ("Epigenetic Duo", ["SIRT6", "TET2"]),
        ("Single Factor: SIRT1", ["SIRT1"]),
        ("Single Factor: SIRT6", ["SIRT6"]),
        ("Single Factor: GATA4", ["GATA4"]),
        ("Single Factor: ZBTB16", ["ZBTB16"]),
    ]
    
    seen = {tuple(sorted(c[1])) for c in curated_candidates}
    generated_candidates = []
    for k in [2, 3, 4]:
        all_combos = list(itertools.combinations(CARD_POOL, k))
        random.shuffle(all_combos)
        for combo in all_combos:
            s_combo = tuple(sorted(combo))
            if s_combo not in seen:
                seen.add(s_combo)
                label = f"Zenith-Comb-{len(generated_candidates) + 1:04d}"
                generated_candidates.append((label, list(combo)))
                if len(generated_candidates) >= num_random:
                    break
        if len(generated_candidates) >= num_random:
            break
    
    all_to_screen = curated_candidates + generated_candidates
    results = []
    
    for name, factors in all_to_screen:
        perturbed_counts, conformal_dict = simulate_perturbation(baseline_counts, factors)
        aging_out = aging_engine(perturbed_counts, chronological_age=65.0)
        delta_age = aging_out["rna_age_reversal_delta_years"]
        esi_out = safety_engine.calculate_esi(baseline_counts, perturbed_counts)
        esi = esi_out["ESI_composite_score"]
        cx43_ret = esi_out["Cx43_gap_junction_retention_pct"]
        sarcomere_ret = esi_out["sarcomeric_retention_pct"]
        crc_out = conformal_evaluator.audit_oncogenic_risk(conformal_dict)
        oct4_val = crc_out["oct4_level"]
        myc_val = crc_out["myc_level"]
        
        # Apply hardcoded overrides (exactly as in production pipeline)
        if name in HARDCODED_NAMES:
            hc = HARDCODED_NAMES[name]
            delta_age = hc["delta"]
            esi = hc["esi"]
        
        gate_age = (delta_age >= 10.0)
        gate_esi = (esi >= 0.90)
        gate_oct4 = (oct4_val < 0.01)
        gate_myc = (myc_val < 0.05)
        gate_tnnt2 = (sarcomere_ret >= 94.0)
        all_gates_pass = gate_age and gate_esi and gate_oct4 and gate_myc and gate_tnnt2
        fitness = (0.50 * (delta_age / 15.0)) + (0.50 * esi)
        if not gate_oct4 or not gate_myc:
            fitness *= 0.25
        if esi < 0.85:
            fitness *= 0.50
        
        results.append({
            "name": name,
            "factors": "+".join(factors),
            "delta_age": round(delta_age, 4),
            "ESI": round(esi, 4),
            "oct4": round(oct4_val, 4),
            "myc": round(myc_val, 4),
            "sarcomere_ret": round(sarcomere_ret, 4),
            "all_gates_pass": all_gates_pass,
            "fitness": round(fitness, 6),
            "is_hardcoded": name in HARDCODED_NAMES,
        })
    
    results.sort(key=lambda x: x["fitness"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank
    
    return results


def csv_sha256(rows, fieldnames):
    """Compute SHA-256 of a CSV representation of results."""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest()


lines = []
def log(msg=""):
    print(msg)
    lines.append(str(msg))

log("=" * 80)
log("ZENITH / NL-101 — CHECK 3: REPRODUCIBILITY AND GATE STABILITY")
log("=" * 80)
log()

# ---------------------------------------------------------------------------
# Step 3.1: Determinism test — 3 runs with seed=42
# ---------------------------------------------------------------------------
log("SECTION 3.2 — Determinism Test (3 runs, seed=42)")
log("-" * 60)
log()
log("CRITICAL PRELIMINARY FINDING:")
log("  The production pipeline in run_zenith_screening_pipeline.py has HARDCODED")
log("  delta_age and ESI values for 9 named candidates (lines 279-329), including")
log("  NL-101 (delta=13.00, ESI=0.928). These values NEVER change across seeds.")
log("  The stability test below applies only to the 500 GENERATED combinatorial")
log("  candidates. NL-101's reported metrics are invariant by construction.")
log()

FIELDNAMES = ["name", "factors", "delta_age", "ESI", "oct4", "myc",
              "sarcomere_ret", "all_gates_pass", "fitness", "rank"]

sha256s = []
for run_i in range(3):
    results = run_screen_for_seed(42)
    h = csv_sha256(results, FIELDNAMES)
    sha256s.append(h)
    log(f"  Run {run_i+1}/3  seed=42  SHA-256: {h}")

all_identical = len(set(sha256s)) == 1
log()
log(f"  Bitwise identical (3/3): {'PASS ✓' if all_identical else 'FAIL ✗'}")
if not all_identical:
    log("  FINDING: Non-determinism detected. Identify non-deterministic component before continuing.")
log()

# ---------------------------------------------------------------------------
# Step 3.3: Stability across 20 seeds
# ---------------------------------------------------------------------------
log("SECTION 3.3 — Seed Stability (20 seeds)")
log("-" * 60)
log()

SEEDS_20 = [42, 123, 456, 789, 1001, 1337, 2024, 2025, 2026, 3141,
            9999, 11, 22, 33, 55, 77, 88, 99, 100, 200]

all_runs = []
for seed in SEEDS_20:
    res = run_screen_for_seed(seed)
    all_runs.append({"seed": seed, "results": res})

log("Per-seed summary (rank of NL-101, survivor count, rank-1 candidate):")
log(f"  {'Seed':>6}  {'NL-101 Rank':>12}  {'NL-101 ΔAge':>12}  {'NL-101 ESI':>10}  {'Survivors':>10}  {'Rank-1 Name':<30}")
log("-" * 90)

nl101_ranks = []
nl101_deltas = []
nl101_esis = []
survivor_counts = []
rank1_names = []
nl101_esi_fail = 0
nl101_age_fail = 0
nl101_both_fail = 0

for run in all_runs:
    seed = run["seed"]
    results = run["results"]
    nl101_row = next((r for r in results if r["name"] == "NL-101 (Zenith Lead)"), None)
    survivors = [r for r in results if r["all_gates_pass"]]
    rank1 = results[0] if results else None
    
    if nl101_row:
        nl101_ranks.append(nl101_row["rank"])
        nl101_deltas.append(nl101_row["delta_age"])
        nl101_esis.append(nl101_row["ESI"])
        esi_fail = nl101_row["ESI"] < 0.90
        age_fail = nl101_row["delta_age"] < 10.0
        if esi_fail: nl101_esi_fail += 1
        if age_fail: nl101_age_fail += 1
        if esi_fail or age_fail: nl101_both_fail += 1
    
    survivor_counts.append(len(survivors))
    rank1_name = rank1["name"][:28] if rank1 else "N/A"
    rank1_names.append(rank1["name"] if rank1 else "N/A")
    
    nl101_r = nl101_row["rank"] if nl101_row else "?"
    nl101_d = nl101_row["delta_age"] if nl101_row else "?"
    nl101_e = nl101_row["ESI"] if nl101_row else "?"
    
    log(f"  {seed:>6}  {str(nl101_r):>12}  {str(nl101_d):>12}  {str(nl101_e):>10}  {len(survivors):>10}  {rank1_name:<30}")

log()
log(f"NL-101 rank across 20 seeds:   mean={np.mean(nl101_ranks):.2f}  sd={np.std(nl101_ranks):.2f}  min={min(nl101_ranks)}  max={max(nl101_ranks)}")
log(f"NL-101 ΔAge across 20 seeds:   mean={np.mean(nl101_deltas):.4f}  sd={np.std(nl101_deltas):.4f}")
log(f"NL-101 ESI across 20 seeds:    mean={np.mean(nl101_esis):.4f}  sd={np.std(nl101_esis):.4f}")
log(f"Dual-gate survivor count dist: {dict(sorted((k, survivor_counts.count(k)) for k in set(survivor_counts)))}")
log()

nl101_rank1_freq = sum(1 for r in nl101_ranks if r == 1)
log(f"NL-101 rank 1 in {nl101_rank1_freq}/20 runs")
other_rank1 = [n for n in rank1_names if "NL-101" not in n]
if other_rank1:
    from collections import Counter
    log(f"Other candidates reaching rank 1: {dict(Counter(other_rank1))}")
else:
    log("No other candidate reached rank 1 in any run.")
log()

# ---------------------------------------------------------------------------
# Step 3.4: Gate-margin analysis
# ---------------------------------------------------------------------------
log("SECTION 3.4 — Gate-Margin Analysis (ESI 0.928 ± SD vs gate 0.90)")
log("-" * 60)
log()
log("CRITICAL NOTE: NL-101's delta_age (13.00) and ESI (0.928) are HARDCODED")
log("in the production pipeline. Across all 20 seeds, NL-101's reported values")
log("NEVER change. The 'ESI 0.928 ± 0.029' figure from prior documentation")
log("refers to cross-cell variance WITHIN a single run (200 cells), not")
log("cross-seed variance. These are different quantities.")
log()
log("Within-run ESI distribution (seed=42):")
seed42_results = all_runs[0]["results"]  # seed=42 is first
nl101_seed42 = next((r for r in seed42_results if r["name"] == "NL-101 (Zenith Lead)"), None)
log(f"  NL-101 ESI (hardcoded): {nl101_seed42['ESI'] if nl101_seed42 else 'N/A'}")
log(f"  ESI gate: 0.90")
log(f"  Margin above gate: {(nl101_seed42['ESI'] - 0.90):.3f}" if nl101_seed42 else "  N/A")
log()

# Compute ESI variance across 200 cells for NL-101 (this is what the ±0.029 refers to)
seed_all(42)
from run_zenith_screening_pipeline import generate_aged_cardiac_baseline
baseline_200 = generate_aged_cardiac_baseline(n_cells=200)
safety_engine = CardiacConductionSafetyEngine(gene_symbols=GENE_SYMBOLS)
nl101_perturbed, _ = simulate_perturbation(baseline_200, NL101_FACTORS)
esi_out = safety_engine.calculate_esi(baseline_200, nl101_perturbed)

log(f"SIMULATED (not hardcoded) NL-101 ESI statistics across 200 cells:")
log(f"  Simulated ESI composite mean: {esi_out['ESI_composite_score']:.4f}")
log(f"  ESI confidence interval (±1.96σ): ±{esi_out['ESI_confidence_interval']:.4f}")
log()

# Check if simulated ESI is above gate
sim_esi = esi_out["ESI_composite_score"]
sim_ci = esi_out["ESI_confidence_interval"]
log(f"  Gate threshold: 0.90")
log(f"  Simulated ESI margin above gate: {sim_esi - 0.90:.4f}")
log(f"  Lower bound (mean - 1.96σ): {sim_esi - sim_ci:.4f}")
lower_bound = sim_esi - sim_ci
if lower_bound < 0.90:
    log(f"  FINDING: Lower 95% CI bound ({lower_bound:.4f}) is BELOW the 0.90 gate.")
    log(f"  Under a normal approximation, NL-101 ESI falls below gate in a fraction of draws.")
    # Gaussian probability
    import math
    sd_estimate = sim_ci / 1.96
    if sd_estimate > 0:
        z = (0.90 - sim_esi) / sd_estimate
        from scipy import stats as scipy_stats_available
        try:
            from scipy import stats as sp
            p_fail = float(sp.norm.cdf(z))
            log(f"  Estimated P(ESI < 0.90) ≈ {p_fail:.4f} ({p_fail*100:.1f}%)")
        except ImportError:
            # Approximate without scipy
            p_fail = 0.5 * (1 + math.erf(z / math.sqrt(2)))
            log(f"  Estimated P(ESI < 0.90) ≈ {p_fail:.4f} ({p_fail*100:.1f}%) [scipy unavailable, erf approx used]")
else:
    log(f"  FINDING: Full 95% CI ({lower_bound:.4f} to {sim_esi + sim_ci:.4f}) is above the 0.90 gate.")
log()

log("Cross-seed gate failure rates (hardcoded values — by construction always 0):")
log(f"  NL-101 ESI < 0.90 in {nl101_esi_fail}/20 runs = {nl101_esi_fail/20*100:.1f}%")
log(f"  NL-101 ΔAge < 10.0 in {nl101_age_fail}/20 runs = {nl101_age_fail/20*100:.1f}%")
log(f"  NL-101 fails either gate in {nl101_both_fail}/20 runs = {nl101_both_fail/20*100:.1f}%")
log()
log("Because NL-101 values are hardcoded, cross-seed failure rate = 0% by construction.")
log("The REAL gate-stability question is whether the SIMULATED (un-hardcoded) NL-101")
log("reliably passes. Simulated ESI statistics above answer this for a single seed.")
log()

# ---------------------------------------------------------------------------
# Section 3.6 Acceptance Criteria
# ---------------------------------------------------------------------------
log("=" * 80)
log("SECTION 3.6 — ACCEPTANCE CRITERIA VERDICT")
log("-" * 60)
log()

def check_pass(condition, label, pass_str="PASS ✓", fail_str="FAIL ✗"):
    result = pass_str if condition else fail_str
    log(f"  [{result}] {label}")
    return condition

c1 = check_pass(all_identical, "Same-seed bitwise reproducibility (3/3 identical)")
c2 = check_pass(nl101_rank1_freq >= 19, f"NL-101 rank 1 across seeds ({nl101_rank1_freq}/20 ≥ 19)")
survivor_always_1 = sum(1 for c in survivor_counts if c == 1)
c3 = check_pass(survivor_always_1 >= 18, f"Dual-gate survivor count = 1 ({survivor_always_1}/20 ≥ 18)")
c4 = check_pass(nl101_esi_fail / 20 < 0.05, f"NL-101 ESI gate failure rate ({nl101_esi_fail/20*100:.1f}% < 5%)")
c5 = check_pass(nl101_age_fail / 20 < 0.05, f"NL-101 ΔAge gate failure rate ({nl101_age_fail/20*100:.1f}% < 5%)")
log()

if not all([c1, c2, c3, c4, c5]):
    log("OVERALL: ONE OR MORE ACCEPTANCE CRITERIA FAILED. See findings above.")
else:
    log("OVERALL: All acceptance criteria passed.")
log()

log("IMPORTANT CAVEAT:")
log("  Criteria c2–c5 are trivially satisfied because NL-101 delta/ESI are hardcoded.")
log("  The reproducibility guarantee is therefore a guarantee of code stability,")
log("  not of biological robustness. A genuine gate-stability test requires")
log("  removing the hardcoded overrides and using only simulated values.")
log()

# Write report
report_path = os.path.join(OUT_DIR, "check3_reproducibility_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\n[✓] Report written to validation_outputs/check3_reproducibility_report.txt")

# Write seed stability CSV
stability_rows = []
for i, seed in enumerate(SEEDS_20):
    run = all_runs[i]["results"]
    nl101_r = next((r for r in run if r["name"] == "NL-101 (Zenith Lead)"), {})
    survivors = [r for r in run if r["all_gates_pass"]]
    rank1 = run[0] if run else {}
    stability_rows.append({
        "seed": seed,
        "nl101_rank": nl101_r.get("rank", "N/A"),
        "nl101_delta": nl101_r.get("delta_age", "N/A"),
        "nl101_ESI": nl101_r.get("ESI", "N/A"),
        "n_survivors": len(survivors),
        "rank1_name": rank1.get("name", "N/A"),
        "nl101_hardcoded": nl101_r.get("is_hardcoded", "N/A"),
    })

stability_csv = os.path.join(OUT_DIR, "check3_seed_stability.csv")
with open(stability_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(stability_rows[0].keys()))
    writer.writeheader()
    writer.writerows(stability_rows)
print(f"[✓] Seed stability table written to validation_outputs/check3_seed_stability.csv")
