import os
import sys
import math
import random
import itertools
from collections import Counter
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")
import numpy as np
import torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

from run_zenith_screening_pipeline import (
    GENE_SYMBOLS, GENE_TO_IDX, NUM_GENES,
    generate_aged_cardiac_baseline,
    simulate_perturbation,
    NativeTranscriptomicAgingEngine,
    CardiacConductionSafetyEngine,
    ThresholdSafetyGate
)

CLOCK_WEIGHTS = {
    "CDKN2A": 2.45, "CDKN1A": 1.48, "IL6": 1.15, "SERPINE1": 1.05, "COL1A1": 0.85,
    "SIRT1": -2.15, "SIRT6": -1.95, "FOXO3": -1.65, "PPARGC1A": -1.45, "GATA4": -1.25,
    "ATP2A2": -1.55, "GJA1": -1.35, "TNNT2": -1.10, "ZBTB16": -1.30, "TET2": -0.95
}

card_pool = ["SIRT1", "SIRT6", "GATA4", "ZBTB16", "FOXO3", "PPARGC1A",
             "MEF2C", "TBX5", "NKX2-5", "HAND2", "ESRRG", "TET2"]

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
]

def build_509_candidates():
    random.seed(SEED)
    seen = {tuple(sorted(c[1])) for c in curated_candidates}
    generated = []
    for k in [2, 3, 4]:
        combos = list(itertools.combinations(card_pool, k))
        random.shuffle(combos)
        for c in combos:
            sc = tuple(sorted(c))
            if sc not in seen:
                seen.add(sc)
                generated.append((f"Zenith-Comb-{len(generated)+1:04d}", list(c)))
                if len(generated) >= 500:
                    break
        if len(generated) >= 500:
            break
    return curated_candidates + generated

all_509 = build_509_candidates()
print(f"Total candidates built: {len(all_509)}")

# Generate baseline
baseline_counts = generate_aged_cardiac_baseline(200)

# Engines
aging_engine = NativeTranscriptomicAgingEngine(GENE_SYMBOLS, CLOCK_WEIGHTS)
safety_engine = CardiacConductionSafetyEngine(GENE_SYMBOLS)
conformal_evaluator = ThresholdSafetyGate(0.01)

# -------------------------------------------------------------
# TEST 2: Cooperative bonus check
# -------------------------------------------------------------
print("\n--- TEST 2 ---")
# 1. Look for SIRT1+SIRT6+FOXO3+PPARGC1A
target_comb = {"SIRT1", "SIRT6", "FOXO3", "PPARGC1A"}
found_target = None
for name, f_list in all_509:
    if set(f_list) == target_comb:
        found_target = (name, f_list)
        break

def run_screen(pert_fn, clock_dict=None):
    if clock_dict is None:
        clock_dict = CLOCK_WEIGHTS
    ag_eng = NativeTranscriptomicAgingEngine(GENE_SYMBOLS, clock_dict)
    res = []
    for name, factors in all_509:
        pert, conf = pert_fn(baseline_counts, factors)
        a_out = ag_eng(pert, 65.0)
        s_out = safety_engine.calculate_esi(baseline_counts, pert)
        c_out = conformal_evaluator.audit_oncogenic_risk(conf)
        
        d_age = a_out["rna_age_reversal_delta_years"]
        esi = s_out["ESI_composite_score"]
        oct4 = c_out["oct4_level"]
        myc = c_out["myc_level"]
        sarc = s_out["sarcomeric_retention_pct"]
        cx43 = s_out["Cx43_gap_junction_retention_pct"]
        
        pass_age = (d_age >= 10.0)
        pass_esi = (esi >= 0.90)
        pass_oct = (oct4 < 0.01)
        pass_myc = (myc < 0.05)
        pass_sarc = (sarc >= 94.0)
        all_pass = (pass_age and pass_esi and pass_oct and pass_myc and pass_sarc)
        
        fitness = (0.50 * (d_age / 15.0)) + (0.50 * esi)
        if not pass_oct or not pass_myc: fitness *= 0.25
        if esi < 0.85: fitness *= 0.50
        
        res.append({
            "name": name,
            "factors": factors,
            "d_age": d_age,
            "esi": esi,
            "cx43": cx43,
            "sarcomere": sarc,
            "oct4": oct4,
            "myc": myc,
            "all_pass": all_pass,
            "fitness": fitness
        })
    res.sort(key=lambda x: x["fitness"], reverse=True)
    for i, r in enumerate(res, 1):
        r["rank"] = i
    return res

# Standard run (with simulate_perturbation as-is)
std_results = run_screen(simulate_perturbation)

if found_target:
    row_target = next(r for r in std_results if set(r["factors"]) == target_comb)
    print(f"Target SIRT1+SIRT6+FOXO3+PPARGC1A found: {row_target['name']}, Rank: {row_target['rank']}, dAge: {row_target['d_age']:.2f}, ESI: {row_target['esi']:.4f}")
else:
    # Not in the 500 random draw, let's explicitly evaluate it
    pert, conf = simulate_perturbation(baseline_counts, list(target_comb))
    a_out = aging_engine(pert, 65.0)
    s_out = safety_engine.calculate_esi(baseline_counts, pert)
    print(f"Target SIRT1+SIRT6+FOXO3+PPARGC1A was not in random 509 draw. Evaluated standalone: dAge = {a_out['rna_age_reversal_delta_years']:.2f}, ESI = {s_out['ESI_composite_score']:.4f}")

# Now define simulate_perturbation WITHOUT ANY BONUSES (zero out lines 105, 108, etc.)
def simulate_perturbation_no_bonus(baseline: torch.Tensor, factors: list) -> tuple:
    perturbed = baseline.clone()
    f_set = {f.upper() for f in factors}
    
    has_sirt1 = "SIRT1" in f_set
    has_sirt6 = "SIRT6" in f_set
    has_zbtb16 = "ZBTB16" in f_set
    has_gata4 = "GATA4" in f_set
    is_yamanaka = ("POU5F1" in f_set or "OCT4" in f_set) and ("SOX2" in f_set)
    
    # Strictly additive per factor: no 0.85 dual sirtuin bonus, no 1.65 NL-101 bonus
    rejuv_multiplier = 0.0
    if has_sirt1: rejuv_multiplier += 1.45
    if has_sirt6: rejuv_multiplier += 1.20
    # Line 105 disabled: if has_sirt1 and has_sirt6: rejuv_multiplier += 0.85
    if has_zbtb16: rejuv_multiplier += 0.90
    # Line 107-108 disabled: if has_sirt1 and has_sirt6 and has_zbtb16 and has_gata4: rejuv_multiplier += 1.65

    # Senescence clearance
    for sen_gene in ["CDKN2A", "CDKN1A", "IL6", "SERPINE1"]:
        if sen_gene in GENE_TO_IDX:
            idx = GENE_TO_IDX[sen_gene]
            suppression = max(0.08, 1.0 - (0.165 * rejuv_multiplier))
            perturbed[:, idx] *= suppression

    # Sirtuin / Longevity upregulation
    for sg in ["SIRT1", "SIRT6", "FOXO3", "PPARGC1A", "ZBTB16"]:
        if sg in GENE_TO_IDX:
            idx = GENE_TO_IDX[sg]
            boost = 1.0 + (0.32 * rejuv_multiplier if (sg in f_set or (sg == "FOXO3" and has_sirt1)) else 0.05)
            perturbed[:, idx] *= boost

    # Cardiac Conduction & Identity Effects
    if has_gata4:
        if "GJA1" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["GJA1"]] *= 1.22
        if "TNNT2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["TNNT2"]] *= 1.12
        if "KCNJ2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["KCNJ2"]] *= 1.10
    else:
        if "GJA1" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["GJA1"]] *= 0.479
        if "TNNT2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["TNNT2"]] *= 0.816
        if "KCNJ2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["KCNJ2"]] *= 0.780

    if "ATP2A2" in GENE_TO_IDX:
        # Linear/proportional SERCA2a boost
        serca_boost = 1.0 + (0.12 if has_sirt1 else 0.0) + (0.12 if has_sirt6 else 0.0)
        perturbed[:, GENE_TO_IDX["ATP2A2"]] *= serca_boost

    oct4_level = 0.008
    myc_level = 0.038
    lin28_level = 0.004

    if is_yamanaka:
        if "GJA1" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["GJA1"]] *= 0.28
        if "TNNT2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["TNNT2"]] *= 0.38
        if "ATP2A2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["ATP2A2"]] *= 0.25
        if "KCNJ2" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["KCNJ2"]] *= 0.22
        oct4_level = 0.460
        lin28_level = 0.310

    if "POU5F1" in f_set or "OCT4" in f_set: oct4_level = max(oct4_level, 0.420)
    if "MYC" in f_set:
        myc_level = 0.380
        if "CDKN2A" in GENE_TO_IDX: perturbed[:, GENE_TO_IDX["CDKN2A"]] *= 1.35
    if "SOX2" in f_set: oct4_level = max(oct4_level, 0.350)

    conformal_dict = {
        "POU5F1": oct4_level,
        "OCT4": oct4_level,
        "MYC": myc_level,
        "LIN28A": lin28_level
    }
    return perturbed, conformal_dict

no_bonus_results = run_screen(simulate_perturbation_no_bonus)
nl101_std = next(r for r in std_results if "NL-101" in r["name"])
nl101_no_bonus = next(r for r in no_bonus_results if "NL-101" in r["name"])

print(f"NL-101 ΔAge WITH bonus: {nl101_std['d_age']:.2f}, Rank: {nl101_std['rank']}")
print(f"NL-101 ΔAge WITHOUT bonus: {nl101_no_bonus['d_age']:.2f}, Rank: {nl101_no_bonus['rank']}")
print("\nTop 10 WITHOUT bonus:")
for r in no_bonus_results[:10]:
    print(f"Rank {r['rank']}: {r['name']} | Factors: {r['factors']} | dAge: {r['d_age']:.2f} | ESI: {r['esi']:.4f} | Pass: {r['all_pass']}")

# -------------------------------------------------------------
# TEST 3: ESI and metric discrimination
# -------------------------------------------------------------
print("\n--- TEST 3 ---")
esi_vals = [r["esi"] for r in std_results]
dage_vals = [r["d_age"] for r in std_results]
cx43_vals = [r["cx43"] for r in std_results]
oct4_vals = [r["oct4"] for r in std_results]
myc_vals = [r["myc"] for r in std_results]

def get_stats(vals):
    u = sorted(list(set(vals)))
    c = Counter(vals)
    most_common_val, most_common_count = c.most_common(1)[0]
    return {
        "num_unique": len(u),
        "unique_values": [round(x, 4) for x in u],
        "std_dev": float(np.std(vals)),
        "mean": float(np.mean(vals)),
        "most_common_val": most_common_val,
        "most_common_count": most_common_count,
        "histogram": {round(k, 4): v for k, v in sorted(c.items())}
    }

print("ESI Stats:", get_stats(esi_vals))
print("dAge Stats: unique count =", len(set(dage_vals)), "std =", np.std(dage_vals))
print("Cx43 Stats:", get_stats(cx43_vals))
print("OCT4 Stats:", get_stats(oct4_vals))
print("MYC Stats:", get_stats(myc_vals))

# -------------------------------------------------------------
# TEST 4: Downstream expression changes
# -------------------------------------------------------------
print("\n--- TEST 4 ---")
pert_nl101, _ = simulate_perturbation(baseline_counts, ["SIRT1", "SIRT6", "GATA4", "ZBTB16"])
base_mean = baseline_counts.mean(dim=0).numpy()
pert_mean = pert_nl101.mean(dim=0).numpy()

changed_genes = []
for i, g in enumerate(GENE_SYMBOLS):
    b = float(base_mean[i])
    p = float(pert_mean[i])
    diff = p - b
    pct = (diff / b) * 100.0 if b != 0 else 0.0
    if abs(diff) > 1e-4:
        changed_genes.append((g, b, p, diff, pct))

print(f"Total genes in panel: {len(GENE_SYMBOLS)}")
print(f"Total genes changed: {len(changed_genes)}")
print("Changed genes list:")
for g, b, p, d, pct in changed_genes:
    print(f"  {g:<10}: before={b:6.3f}, after={p:6.3f}, diff={d:+6.3f} ({pct:+6.1f}%)")

# Decompose clock score into factor genes vs other genes
# clock_shift = sum(log(1 + expr_i) * w_i) * 1.85
log_b = np.log1p(base_mean)
log_p = np.log1p(pert_mean)

factor_shift = 0.0
other_shift = 0.0

for g, w in CLOCK_WEIGHTS.items():
    idx = GENE_TO_IDX[g]
    delta_log = log_p[idx] - log_b[idx]
    contrib = delta_log * w * 1.85 # in years of predicted_rna_age shift (note: negative shift = younger = positive reversal)
    # Reversal contribution is -contrib
    reversal_contrib = -contrib
    if g in ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]:
        factor_shift += reversal_contrib
    else:
        other_shift += reversal_contrib

total_reversal_shift = factor_shift + other_shift
print(f"Decomposition of ΔAge shift:")
print(f"  Factor genes contribution (SIRT1, SIRT6, GATA4, ZBTB16): {factor_shift:+.3f}y ({factor_shift/total_reversal_shift*100:.1f}%)")
print(f"  Other genes contribution (senescence + markers):        {other_shift:+.3f}y ({other_shift/total_reversal_shift*100:.1f}%)")
print(f"  Total reconstructed shift:                              {total_reversal_shift:+.3f}y")

# -------------------------------------------------------------
# TEST 5: Zero-weight circularity test
# -------------------------------------------------------------
print("\n--- TEST 5 ---")
clock_zeroed = dict(CLOCK_WEIGHTS)
for fg in ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]:
    clock_zeroed[fg] = 0.0

res_zeroed = run_screen(simulate_perturbation, clock_dict=clock_zeroed)
nl101_zeroed = next(r for r in res_zeroed if "NL-101" in r["name"])
survivors_zeroed = [r for r in res_zeroed if r["all_pass"]]

print(f"NL-101 ΔAge with original clock: {nl101_std['d_age']:.2f}")
print(f"NL-101 ΔAge with four factor weights ZEROED: {nl101_zeroed['d_age']:.2f}")
print(f"NL-101 Rank with zeroed clock: {nl101_zeroed['rank']}")
print(f"Dual-gate survivors count under zeroed clock: {len(survivors_zeroed)}")
print("Top 5 under zeroed clock:")
for r in res_zeroed[:5]:
    print(f"  Rank {r['rank']}: {r['name']} | dAge: {r['d_age']:.2f} | ESI: {r['esi']:.4f} | Pass: {r['all_pass']}")

# -------------------------------------------------------------
# TEST 6: Shuffle test (100 permutations)
# -------------------------------------------------------------
print("\n--- TEST 6 ---")
random.seed(SEED)
nl101_rank1_count = 0
nl101_survivor_count = 0
winner_counts = Counter()

genes_15 = list(CLOCK_WEIGHTS.keys())
weights_15 = list(CLOCK_WEIGHTS.values())

for iter_i in range(100):
    shuffled_w = list(weights_15)
    random.shuffle(shuffled_w)
    perm_clock = dict(zip(genes_15, shuffled_w))
    
    res_perm = run_screen(simulate_perturbation, clock_dict=perm_clock)
    nl101_r = next(r for r in res_perm if "NL-101" in r["name"])
    if nl101_r["rank"] == 1:
        nl101_rank1_count += 1
    if nl101_r["all_pass"]:
        nl101_survivor_count += 1
    winner = res_perm[0]
    winner_counts[winner["name"]] += 1

print(f"Across 100 random clock weight permutations:")
print(f"  NL-101 Rank 1 frequency: {nl101_rank1_count}/100")
print(f"  NL-101 Dual-gate survivor frequency: {nl101_survivor_count}/100")
print("  Top winners distribution:", winner_counts.most_common(5))

# -------------------------------------------------------------
# TEST 7: Null distribution
# -------------------------------------------------------------
print("\n--- TEST 7 ---")
random.seed(SEED)
# 200 random 4-gene combos from 50 GENE_SYMBOLS
null_50_dages = []
null_50_passes = 0
for _ in range(200):
    c = random.sample(GENE_SYMBOLS, 4)
    pert, conf = simulate_perturbation(baseline_counts, c)
    a_out = aging_engine(pert, 65.0)
    s_out = safety_engine.calculate_esi(baseline_counts, pert)
    c_out = conformal_evaluator.audit_oncogenic_risk(conf)
    da = a_out["rna_age_reversal_delta_years"]
    es = s_out["ESI_composite_score"]
    pass_all = (da >= 10.0 and es >= 0.90 and c_out["oct4_level"] < 0.01 and c_out["myc_level"] < 0.05 and s_out["sarcomeric_retention_pct"] >= 94.0)
    null_50_dages.append(da)
    if pass_all: null_50_passes += 1

# 200 random 4-gene combos from 12 card_pool
all_card_4 = list(itertools.combinations(card_pool, 4))
card_4_dages = []
card_4_passes = 0
for c in all_card_4:
    pert, conf = simulate_perturbation(baseline_counts, list(c))
    a_out = aging_engine(pert, 65.0)
    s_out = safety_engine.calculate_esi(baseline_counts, pert)
    c_out = conformal_evaluator.audit_oncogenic_risk(conf)
    da = a_out["rna_age_reversal_delta_years"]
    es = s_out["ESI_composite_score"]
    pass_all = (da >= 10.0 and es >= 0.90 and c_out["oct4_level"] < 0.01 and c_out["myc_level"] < 0.05 and s_out["sarcomeric_retention_pct"] >= 94.0)
    card_4_dages.append(da)
    if pass_all: card_4_passes += 1

nl101_da = nl101_std["d_age"]
pct_50 = sum(1 for x in null_50_dages if x < nl101_da) / len(null_50_dages) * 100.0
pct_card = sum(1 for x in card_4_dages if x < nl101_da) / len(card_4_dages) * 100.0

print(f"Null 50-gene pool: min={min(null_50_dages):.2f}, max={max(null_50_dages):.2f}, mean={np.mean(null_50_dages):.2f}, passes={null_50_passes}/200, NL-101 percentile={pct_50:.1f}%")
print(f"12-gene card pool ({len(card_4_dages)} combos): min={min(card_4_dages):.2f}, max={max(card_4_dages):.2f}, mean={np.mean(card_4_dages):.2f}, passes={card_4_passes}/{len(card_4_dages)}, NL-101 percentile={pct_card:.1f}%")

# -------------------------------------------------------------
# TEST 8: Weight sensitivity (±20% jitter)
# -------------------------------------------------------------
print("\n--- TEST 8 ---")
random.seed(SEED)
sens_rank1 = 0
sens_passes = 0
sens_dages = []

for _ in range(100):
    jitter_clock = {}
    for g, w in CLOCK_WEIGHTS.items():
        factor = 1.0 + random.uniform(-0.20, 0.20)
        jitter_clock[g] = w * factor
    
    res_jit = run_screen(simulate_perturbation, clock_dict=jitter_clock)
    nl_jit = next(r for r in res_jit if "NL-101" in r["name"])
    sens_dages.append(nl_jit["d_age"])
    if nl_jit["rank"] == 1: sens_rank1 += 1
    if nl_jit["all_pass"]: sens_passes += 1

ci_lower = float(np.percentile(sens_dages, 2.5))
ci_upper = float(np.percentile(sens_dages, 97.5))
print(f"Weight sensitivity ±20% (100 runs):")
print(f"  Rank 1 frequency: {sens_rank1}/100")
print(f"  Dual-gate pass frequency: {sens_passes}/100")
print(f"  NL-101 ΔAge mean={np.mean(sens_dages):.2f}, 95% CI: [{ci_lower:.2f}, {ci_upper:.2f}]")

