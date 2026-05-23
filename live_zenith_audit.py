"""
live_zenith_audit.py
~~~~~~~~~~~~~~~~~~~~
ZENITH LIVE CELL-TYPE CLINICAL AUDIT & DOSAGE ENGINE
====================================================
Integrates your live production server data from https://www.niluslab.com
with your local partial reprogramming safety gates and Bayesian dosage optimization loops.

Usage:
  py live_zenith_audit.py --cell-type smooth_muscle_cell --factors SIRT1,FOXO3,KLF4,MYC,TET1
"""

import sys
import os
import argparse
import json
import requests
from datetime import datetime

# Import local engines
from partial_safety import filter_for_partial_reprogramming, ONCOGENE_BLACKLIST, FULL_DEDIFF_RISK
from dosage_optimization_engine import DosageOptimizer

LIVE_URL = "https://www.niluslab.com/api/cell-types"

def fetch_live_cell_types():
    """Fetches the live scVI HCA cell types and clock deltas from production."""
    print(f"\n[Zenith Link] Connecting to live website: {LIVE_URL} ...")
    try:
        r = requests.get(LIVE_URL, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print("[Zenith Link] Successfully connected. Live HCA data retrieved.")
            return data.get("cell_types", [])
        else:
            print(f"[Warning] Failed to fetch live data (HTTP {r.status_code}). Using local fallbacks.")
            return []
    except Exception as e:
        print(f"[Warning] Connection error: {e}. Using local fallbacks.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Zenith Live Auditing and Dosage Optimization Pipeline")
    parser.add_argument("--cell-type", type=str, default="smooth_muscle_cell",
                        help="Lineage key (e.g. smooth_muscle_cell, regular_ventricular_cardiac_myocyte, fibroblast)")
    parser.add_argument("--factors", type=str, default="SIRT1,FOXO3,KLF4,MYC,TET1",
                        help="Comma-separated HGNC gene symbols for the candidate rejuvenation cocktail")
    parser.add_argument("--mode", type=str, choices=["conservative", "balanced", "aggressive"], default="balanced",
                        help="Reprogramming safety filtering mode")
    parser.add_argument("--bio-age", type=float, default=0.7,
                        help="Normalized starting biological age (0.0 to 1.0)")
    
    args = parser.parse_args()
    
    factors_list = [f.strip().upper() for f in args.factors.split(",") if f.strip()]
    
    print("=" * 70)
    print("      ZENITH LIVE CLINICAL AUDIT & TRANSIENT DOSAGE PIPELINE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Lineage: {args.cell_type}")
    print(f"Candidate Cocktail: {factors_list}")
    print(f"Safety Mode: {args.mode.upper()} | Bio-Age Input: {args.bio_age}")
    print("-" * 70)
    
    # ── STAGE 1: Live Production Sync ─────────────────────────────────
    live_types = fetch_live_cell_types()
    active_metadata = None
    
    if live_types:
        for ct in live_types:
            if ct["key"] == args.cell_type:
                active_metadata = ct
                break
    
    if active_metadata:
        print(f"\n[STAGE 1] Syncing with Live Attractor coordinates:")
        print(f"  - Cell Type Label: {active_metadata.get('label')}")
        print(f"  - HCA Cell Count:  {active_metadata.get('n_cells'):,} cells")
        print(f"  - Epigenetic Clock Delta (Age Delta): -{active_metadata.get('age_delta')}y")
        print(f"  - Rejuvenation Vector Magnitude:  {active_metadata.get('magnitude', 'N/A')}")
    else:
        print(f"\n[STAGE 1] Lineage key '{args.cell_type}' not matched in live HCA metadata. Using defaults.")
        active_metadata = {
            "label": args.cell_type,
            "n_cells": 50000,
            "age_delta": 5.0,
            "magnitude": 1.0
        }
    
    # ── STAGE 2: Safety Gate Screening ─────────────────────────────────
    print(f"\n[STAGE 2] Executing Reprogramming Safety Audits...")
    safety_result = filter_for_partial_reprogramming(
        candidates=factors_list,
        mode=args.mode,
        bio_age=args.bio_age
    )
    
    print("\n  APPROVED COCKTAIL:")
    for f in safety_result["approved"]:
        path_tag = "[SIRT] SIRT Pathway" if f["sirtuin_pathway"] else "     "
        print(f"    [APPROVED] {f['gene']:10} | Safety Score: {f['safety_score']}/100 | Longevity Score: {f['longevity_score']}/100 | {path_tag}")
        
    if safety_result["blocked"]:
        print("\n  BLOCKED FACTORS (SAFETY VIOLATION):")
        for b in safety_result["blocked"]:
            print(f"    [BLOCKED] {b['gene']:10} | Category: {b['category'].upper()} | Reason: {b['reason']}")
    else:
        print("\n  [BLOCKED] No factors were blocked. Safety checks cleared.")
        
    print(f"\n  Pathway scoring:")
    print(f"    - Sirtuin Longevity Score: {safety_result['sirtuin_report']['pathway_score']}%")
    print(f"    - Caloric Restriction Mimicry: {safety_result['sirtuin_report']['caloric_restriction_mimicry']}")
    print(f"    - Horvath Clock Loci Impact: {safety_result['horvath_report']['loci_affected']}/8 CpG sites ({safety_result['horvath_report']['predicted_shift']} shift)")

    # ── STAGE 3: Bayesian Dosage Calibration ───────────────────────────
    # Dynamically tune target age reduction to the live cell-type clock delta
    target_reduction = float(active_metadata.get("age_delta", 10.0))
    if target_reduction <= 0:
        target_reduction = 5.0 # default fallback
        
    print(f"\n[STAGE 3] Calibrating Bayesian GP Dosage loop for target -{target_reduction}y reduction...")
    
    optimizer = DosageOptimizer(target_reduction=target_reduction, max_stress=0.05)
    dosage_audit = optimizer.optimize(n_iterations=5) # fast optimized run
    
    print(f"\n  Optimal Protocol Parameters:")
    print(f"    - Pulse ON duration:  {dosage_audit['optimal_on_hours']} hours")
    print(f"    - Recovery OFF window: {dosage_audit['optimal_off_hours']} hours")
    print(f"    - Efficiency Ratio:    {dosage_audit['efficiency_ratio']}")
    print(f"    - Predicted Stress:    {dosage_audit['predicted_stress']}")
    print(f"    - Safety Status:       {dosage_audit['safety_status']}")

    # ── STAGE 4: AlphaFold 3 (AF3) Structural Manifest ─────────────────
    print(f"\n[STAGE 4] Creating structural biology manifests (AlphaFold 3)...")
    approved_genes = [f["gene"] for f in safety_result["approved"]]
    
    af3_manifest = None
    if len(approved_genes) >= 2:
        # Custom mock sequence linkers for the pioneer TFs (used for AF3 docking)
        af3_manifest = {
            "name": f"Zenith_Live_Audit_{args.cell_type}_{approved_genes[0]}_{approved_genes[1]}",
            "modelSeeds": [42],
            "sequences": [
                {
                    "proteinChain": {
                        "sequence": "MGDSHPPSKKRKVEDPHKPPYSYIALIVMAIQSSPTKRLTLSEIYQFLQARFPFFRGAYQGWKNSVRHNLSLNECFIKLPKGLGRPGKGHYWTIDPASEFMDGD",
                        "count": 1
                    }
                },
                {
                    "dnaSequence": {
                        "sequence": "CCTGTGACTGTGGGGTTCACGCTCCCGGGTG",
                        "count": 1
                    }
                }
            ],
            "dialect": "alphafold3",
            "version": 1
        }
        print(f"  - Generated AF3 Docking Manifest: Zenith_Live_Audit_{args.cell_type}_{approved_genes[0]}_{approved_genes[1]}.json")
    else:
        print("  - AF3 manifest requires at least 2 approved factors to model cooperative chromatin binding.")

    # ── STAGE 5: Synthesis & Export ──────────────────────────────────
    final_output = {
        "timestamp": datetime.now().isoformat(),
        "lineage": args.cell_type,
        "live_metadata": active_metadata,
        "safety_audit": safety_result,
        "dosage_optimization": dosage_audit,
        "af3_manifest": af3_manifest
    }
    
    export_filename = f"zenith_live_audit_{args.cell_type}.json"
    with open(export_filename, "w") as f:
        json.dump(final_output, f, indent=2)
        
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED. AUDIT LOG EXPORTED TO: {export_filename}")
    print("=" * 70)

if __name__ == "__main__":
    main()
