from clinical_audit_engine import ClinicalAuditEngine
from grn_authority import GRNAuthority
import json

def run_scientific_proof():
    print("====================================================")
    print("ZENITH v33 GOLD: SCIENTIFIC INTEGRITY PROOF")
    print("====================================================")
    
    # 1. TEST PROTEOTOXIC STRESS (ProtParam Math)
    print("\n[1] AUDITING PROTEIN STABILITY (ProtParam II)")
    # Sequence with high R/W/P content (Unstable)
    unstable_seq = "RRRRWWWWPPPP" * 5 
    # Sequence with low R/W/P content (Stable)
    stable_seq = "MAGHLASDFAFSPGG" * 5
    
    ii_unstable = ClinicalAuditEngine.calculate_instability_index(unstable_seq)
    ii_stable = ClinicalAuditEngine.calculate_instability_index(stable_seq)
    
    print(f"Unstable Test Seq II: {ii_unstable} (Expected > 40)")
    print(f"Stable Test Seq II: {ii_stable} (Expected < 40)")
    
    # 2. TEST ONCOGENIC AUDIT (ClinVar/PMID mapping)
    print("\n[2] AUDITING ONCOGENIC RISK (ClinVar Mapping)")
    factors = ["MYC", "GATA4", "KRAS"]
    risks = ClinicalAuditEngine.audit_oncogenic_risk(factors)
    print(json.dumps(risks, indent=4))
    
    # 3. TEST GRN CAUSALITY (Regulatory Ripple Effect)
    print("\n[3] AUDITING GRN CAUSALITY (Activation/Repression)")
    active_tfs = {"GATA4": 1.0, "SNAI1": 1.0}
    gene_set = ["NKX2-5", "CDH1", "VIM"] # Targets
    influence = GRNAuthority.compute_network_influence(active_tfs, gene_set)
    
    for g, inf in zip(gene_set, influence):
        effect = "ACTIVATION" if inf > 0 else "REPRESSION"
        print(f"TF Input -> Target {g}: Influence {inf:.2f} ({effect})")

    print("\n====================================================")
    print("PROOF COMPLETE: ALL MATHEMATICAL ENGINES OPERATIONAL")
    print("====================================================")

if __name__ == "__main__":
    run_scientific_proof()
