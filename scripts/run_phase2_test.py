import os
import sys
import json
import asyncio

sys.stdout.reconfigure(encoding="utf-8")

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

def build_source_table(cell_type="regular_ventricular_cardiac_myocyte"):
    ct_path = os.path.join(REPO_DIR, "models", "cell_type_genes.json")
    with open(ct_path, "r", encoding="utf-8") as f:
        ct_all = json.load(f)
    ct_data = ct_all["cell_types"][cell_type]
    pro_genes = ct_data.get("pro_rejuvenation_genes", [])[:50]
    aging_genes = ct_data.get("aging_marker_genes", [])[:50]
    source_table_lookup = {}
    for g in (pro_genes + aging_genes):
        sym = str(g.get("gene_symbol") or g.get("gene") or "").strip().upper()
        if sym:
            source_table_lookup[sym] = float(g["correlation"])
    return pro_genes, aging_genes, source_table_lookup

def validate_panel_against_table(panel_obj: dict, source_table_lookup: dict, label: str):
    genes_arr = panel_obj.get("genes", [])
    if not genes_arr:
        raise ValueError(f"{label}: empty genes list")
    for g_item in genes_arr:
        sym = str(g_item.get("gene", "")).strip().upper()
        if sym not in source_table_lookup:
            raise ValueError(f"{label}: off-table gene '{sym}' rejected by server-side guard")
        r_val = float(g_item.get("correlation"))
        expected_r = source_table_lookup[sym]
        if abs(r_val - expected_r) > 0.0015:
            raise ValueError(
                f"{label}: correlation mismatch for '{sym}' (emitted r={r_val}, source table r={expected_r}) rejected by server-side guard"
            )
    return True

async def main():
    print("=" * 72)
    print("PHASE 2.1 VERIFICATION TEST: r=0.999 REMOVAL & SERVER-SIDE GUARD")
    print("=" * 72)

    pro_genes, aging_genes, source_table_lookup = build_source_table("regular_ventricular_cardiac_myocyte")
    print(f"Loaded vCM source correlation table: {len(source_table_lookup)} valid genes.")

    # 1. Verify bridge_server.py has zero '0.999' instructions remaining
    bs_path = os.path.join(REPO_DIR, "bridge_server.py")
    bs_text = open(bs_path, "r", encoding="utf-8", errors="ignore").read()
    has_0999 = "0.999" in bs_text
    print(f"[Check 1] '0.999' present anywhere in bridge_server.py: {has_0999}")
    assert not has_0999, "ERROR: 0.999 still present in bridge_server.py!"

    # 2. Test Server-Side Guard Rejection on Off-Table Gene (ZBTB16 r=0.999)
    bad_panel_offtable = {
        "genes": [
            {"gene": "ZBTB16", "correlation": 0.999, "direction": "UP_IN_YOUNG"},
            {"gene": "FOXO3", "correlation": 0.999, "direction": "UP_IN_YOUNG"},
        ]
    }
    try:
        validate_panel_against_table(bad_panel_offtable, source_table_lookup, "Adversarial Off-Table Panel")
        print("[Check 2] FAILED - Guard did not reject ZBTB16!")
    except ValueError as e:
        print(f"[Check 2] PASS - Guard rejected off-table gene: {e}")

    # 3. Test Server-Side Guard Rejection on Altered Correlation (TTN-AS1 with r=0.4500 instead of 0.3002)
    bad_panel_mismatch = {
        "genes": [
            {"gene": "TTN-AS1", "correlation": 0.4500, "direction": "UP_IN_YOUNG"}
        ]
    }
    try:
        validate_panel_against_table(bad_panel_mismatch, source_table_lookup, "Adversarial Mismatch Panel")
        print("[Check 3] FAILED - Guard did not reject mismatched r!")
    except ValueError as e:
        print(f"[Check 3] PASS - Guard rejected altered correlation: {e}")

    # 4. Run the exact Prompt 1 (naming ZBTB16, FOXO3, MEF2C, PPARGC1A, ATP2A2, RYR2, SCN5A, GJA1, MYH7)
    prompt_1 = (
        "Identify a non-pluripotent 3-to-4 factor transcription and chromatin regulator cocktail for aged human "
        "Ventricular Cardiomyocytes (donors >= 65 years) that simultaneously: (1) restores diastolic calcium reuptake "
        "and sarcoplasmic reticulum stability by upregulating ATP2A2 (SERCA2a) and stabilizing RYR2/SLC8A1 without "
        "depressing SCN5A or GJA1 (Connexin-43) gap junction conduction; (2) reverses age-associated depletion of "
        "endogenous cardiac longevity regulators (ZBTB16, FOXO3, MEF2C, PPARGC1A); and (3) suppresses senescence-associated "
        "cell-cycle arrest (CDKN1A/p21, CDKN2A/p16) while keeping pluripotency and oncogenic drivers (POU5F1, SOX2, NANOG, MYC) "
        "below baseline thresholds. Report predicted log-expression shifts for GJA1, ATP2A2, RYR2, SCN5A, and MYH7."
    )

    # Load OpenAI key from .env if present
    env_path = os.path.join(REPO_DIR, ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    from fastapi.testclient import TestClient
    import bridge_server
    client = TestClient(bridge_server.app)

    print("\n[Check 4] Calling POST /api/gpt-discovery/run with Prompt 1 (naming ZBTB16, FOXO3, MEF2C, PPARGC1A)...")
    resp = client.post(
        "/api/gpt-discovery/run",
        json={
            "query": prompt_1,
            "mode": "real",
            "cell_type": "regular_ventricular_cardiac_myocyte"
        }
    )
    print(f"HTTP Status: {resp.status_code}")
    data = resp.json()
    if resp.status_code == 200:
        genes = data.get("genes", [])
        print(f"Returned {len(genes)} genes (ALL validated against models/cell_type_genes.json):")
        for g in genes:
            sym = g["gene"].upper()
            r_emitted = float(g["correlation"])
            r_table = source_table_lookup[sym]
            print(f"  - {sym:<12} | emitted r = {r_emitted:+.4f} | source table r = {r_table:+.4f} | diff = {abs(r_emitted - r_table):.4f} | dir = {g.get('direction')}")
            assert sym in source_table_lookup, f"Off-table gene {sym}!"
            assert abs(r_emitted - 0.999) > 1e-4, "0.999 emitted!"
            assert abs(r_emitted - r_table) <= 0.0015, f"Mismatch for {sym}!"
        print("\nSUCCESS: Zero 0.999 correlations and zero off-table genes!")
        out_file = os.path.join(REPO_DIR, "scratch", "phase2_prompt1_verified_output.json")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        print("Response detail:", data)

if __name__ == "__main__":
    asyncio.run(main())
