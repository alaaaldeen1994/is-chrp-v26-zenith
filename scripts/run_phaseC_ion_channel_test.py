"""
Phase C Verification Script: Ion-Channel Ensembl-to-Symbol Mapping Fix
Tests PerturbationEngine + NeurosSubstrateService across 3 distinct cocktails
and compares against the pre-fix constant baseline.
"""
import json
from perturbation_engine import PerturbationEngine
from services.neuros_substrate_service import get_substrate_service

def main():
    perts = PerturbationEngine()
    perts.initialize()
    svc = get_substrate_service()

    protected_11 = [
        "SCN5A", "KCNH2", "KCNQ1", "KCNJ2", "CACNA1C",
        "HCN4", "RYR2", "KCNA5", "KCND3", "KCNIP2", "SLC8A1"
    ]
    print("=== 1. PROTECTED 11 ION CHANNELS RESOLUTION IN gene_to_idx ===")
    for g in protected_11 + ["GJA5"]:
        idx = perts.gene_to_idx.get(g)
        ens = perts.var_names[idx] if idx is not None else "NONE"
        print(f"  {g:<8} -> resolved={idx is not None} | idx={str(idx):<5} | ensembl={ens}")

    # Old constant baseline (when all lookups failed and defaulted to 0.0 -> HEALTHY_BASELINES)
    old_zero_expr = {g: 0.0 for g in svc.substrate.ION_CHANNEL_GENES}
    old_audit = svc.substrate.audit_arrhythmia_risk(old_zero_expr)
    old_fib = svc.substrate.check_fibrillation_risk(old_zero_expr)
    print("\n=== 2. OLD CONSTANT BASELINE (PRE-FIX: 0/16 RESOLVED -> 0.0) ===")
    print(f"  phi_hat={old_audit['phi_hat']:.6f} | synchrony={old_audit['synchrony']:.6f} | isi_var={old_fib['isi_variance']:.4f}")

    cocktails = [
        ("Cocktail_1_NL101", ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]),
        ("Cocktail_2_TopGRN", ["NFKB1", "MITF", "CTCF", "HIF1A"]),
        ("Cocktail_3_IonGain", ["SCN5A", "KCNH2", "CACNA1C", "RYR2"]),
    ]

    results = {
        "old_constant_baseline": {
            "phi_hat": round(old_audit["phi_hat"], 6),
            "synchrony": round(old_audit["synchrony"], 6),
            "isi_variance": round(old_fib["isi_variance"], 4),
            "ion_expr_resolved_count": 0,
        },
        "cocktails": {}
    }

    print("\n=== 3. POST-FIX EVALUATION ACROSS 3 DISTINCT COCKTAILS ===")
    for name, factors in cocktails:
        out = perts.predict_factor_effect(factors=factors, source_type="Fibroblast", target_type="Cardiomyocyte", dose=3.0)
        expr_arr = out["predicted_expression"]
        ion_expr = {}
        for g in svc.substrate.ION_CHANNEL_GENES:
            idx = perts.gene_to_idx.get(g.upper())
            ion_expr[g] = round(float(expr_arr[idx]), 5) if idx is not None else 0.0

        audit = svc.substrate.audit_arrhythmia_risk(ion_expr)
        fib = svc.substrate.check_fibrillation_risk(ion_expr)
        resolved_non_zero = {k: v for k, v in ion_expr.items() if v > 0.0}

        results["cocktails"][name] = {
            "factors": factors,
            "resolved_channels_count": len(resolved_non_zero),
            "resolved_ion_expr": resolved_non_zero,
            "classification": audit["safety_classification"],
            "reason": audit["reason"],
            "phi_hat": round(audit["phi_hat"], 6),
            "synchrony": round(audit["synchrony"], 6),
            "active_fraction": round(audit["active_fraction"], 4),
            "isi_variance": round(fib["isi_variance"], 4),
            "blacklist_flags": audit["blacklist_flags"],
        }
        print(f"\n[{name}] ({'+'.join(factors)})")
        print(f"  Resolved channels: {len(resolved_non_zero)} / {len(svc.substrate.ION_CHANNEL_GENES)}")
        print(f"  SCN5A={ion_expr['SCN5A']:.4f}, KCNH2={ion_expr['KCNH2']:.4f}, CACNA1C={ion_expr['CACNA1C']:.4f}, RYR2={ion_expr['RYR2']:.4f}, KCNQ1={ion_expr['KCNQ1']:.4f}")
        print(f"  Classification: {audit['safety_classification']} | phi_hat={audit['phi_hat']:.6f} | synchrony={audit['synchrony']:.6f} | isi_var={fib['isi_variance']:.4f}")

    with open("scratch/phaseC_ion_channel_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
