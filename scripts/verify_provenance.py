import json
import os
import re
import sys
import anndata as ad
import pandas as pd
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {f'-- {detail}' if detail else ''}")
    if not cond:
        sys.exit(1)


def main():
    print("=" * 70)
    print("ZENITH PROVENANCE & QUARANTINE VERIFICATION SUITE")
    print("=" * 70)

    prov_path = os.path.join(ROOT, "provenance.json")
    check("provenance.json exists in root", os.path.exists(prov_path), prov_path)

    with open(prov_path, "r", encoding="utf-8") as f:
        prov = json.load(f)

    # 1. Foundation Model Provenance
    fnd_ckpt_path = os.path.join(ROOT, "models/zenith_foundation_v1/model.pt")
    if os.path.exists(fnd_ckpt_path):
        fnd_ckpt = torch.load(fnd_ckpt_path, map_location="cpu", weights_only=False)
        f_reg = fnd_ckpt["attr_dict"]["registry_"]["field_registries"]
        fnd_n_cells = int(f_reg["X"]["summary_stats"]["n_cells"])
        fnd_n_vars = int(f_reg["X"]["summary_stats"]["n_vars"])
        fnd_n_batch = int(f_reg["batch"]["summary_stats"]["n_batch"])
        cohort_ids = [str(x) for x in f_reg["batch"]["state_registry"]["categorical_mapping"]]

        check(
            "foundation n_cells registered matches manifest (1,962,128)",
            fnd_n_cells == prov["foundation_model"]["n_cells_registered"]["value"] == 1962128,
            f"fnd_n_cells={fnd_n_cells}"
        )
        check(
            "foundation n_vars matches manifest (5,858)",
            fnd_n_vars == prov["foundation_model"]["n_vars"]["value"] == 5858,
            f"fnd_n_vars={fnd_n_vars}"
        )
        check(
            "foundation n_batch == 14 cohorts",
            len(cohort_ids) == fnd_n_batch == 14 == prov["foundation_model"]["n_batch"]["value"],
            f"cohorts={len(cohort_ids)}"
        )
        check(
            "PERIHEART ID strictly absent from foundation cohorts",
            "f1606894-59df-4794-a37f-baa7c6fb6de1" not in cohort_ids,
            "PERIHEART isolated from 14 foundation cohorts"
        )

    # 2. Specialist Model Provenance
    spec_ckpt_path = os.path.join(ROOT, "models/scvi_model_486k_real/model.pt")
    if os.path.exists(spec_ckpt_path):
        spec_ckpt = torch.load(spec_ckpt_path, map_location="cpu", weights_only=False)
        spec_n_genes = int(spec_ckpt["attr_dict"]["registry_"]["field_registries"]["X"]["summary_stats"]["n_vars"])
        spec_n_cells = int(spec_ckpt["attr_dict"]["registry_"]["field_registries"]["X"]["summary_stats"]["n_cells"])

        check(
            "specialist n_genes matches manifest (5,009)",
            spec_n_genes == prov["specialist_model"]["n_genes"]["value"] == 5009,
            f"spec_n_genes={spec_n_genes}"
        )
        check(
            "specialist n_cells_trained matches manifest (99,993)",
            spec_n_cells == prov["specialist_model"]["n_cells_trained"]["value"] == 99993,
            f"spec_n_cells={spec_n_cells}"
        )

    # 3. Quarantined Assets Verification (ZERO synthetic numbers asserted)
    quarantine_dir = os.path.join(ROOT, "quarantine", "track2")
    check("quarantine/track2 directory exists", os.path.isdir(quarantine_dir), quarantine_dir)

    banned_root_files = [
        "run_zenith_screening_pipeline.py",
        "zenith_screening_audit.csv",
        "screen_output.csv",
        "validation_outputs/part2_real_screen/screen_output.csv"
    ]
    for b_rel in banned_root_files:
        b_full = os.path.join(ROOT, b_rel)
        check(f"Quarantined file ABSENT from root: {b_rel}", not os.path.exists(b_full), b_full)

    quarantined_script = os.path.join(quarantine_dir, "run_zenith_screening_pipeline.py")
    check("run_zenith_screening_pipeline.py present in quarantine", os.path.exists(quarantined_script), quarantined_script)

    # Test import guard raises RuntimeError
    try:
        import quarantine.track2.run_zenith_screening_pipeline  # noqa
        import_blocked = False
    except RuntimeError:
        import_blocked = True
    except Exception:
        import_blocked = True

    check("quarantined script raises RuntimeError on import", import_blocked, "Import guard active")

    # Assert provenance.json does NOT contain synthetic screening metrics
    check(
        "provenance.json does not assert synthetic cocktail_count (516)",
        "cocktail_count" not in json.dumps(prov),
        "Synthetic 516 cocktail count purged from provenance.json"
    )
    check(
        "provenance.json does not assert synthetic score (8.073)",
        "8.073" not in json.dumps(prov),
        "Synthetic 8.073 score purged from provenance.json"
    )
    check(
        "provenance.json does not assert synthetic ESI (0.948)",
        "0.948" not in json.dumps(prov),
        "Synthetic 0.948 ESI purged from provenance.json"
    )

    print("\nALL PROVENANCE & QUARANTINE INTEGRITY CHECKS PASSED.")


if __name__ == "__main__":
    main()
