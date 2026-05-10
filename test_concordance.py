import numpy as np
from perturbation_engine import PerturbationEngine

def test_gmt_bench():
    print("[Bench] Initializing Engine...")
    pe = PerturbationEngine()
    pe.initialize()
    
    # GMT Factors
    factors = ["GATA4", "MEF2C", "TBX5"]
    print(f"[Bench] Predicting effect of {factors} on Fibroblasts...")
    
    res = pe.predict_factor_effect(factors, source_type="Fibroblast", target_type="Cardiomyocyte", dose=1.0)
    
    predicted_degs = set(res["top_DEGs"].keys())
    
    # Gold Standard (canonical cardiomyocyte markers)
    gmt_gold = {"TNNT2", "MYH7", "NPPA", "ACTN2", "GATA4", "MEF2C", "TBX5", "RYR2", "PLN", "MYL2"}
    
    intersection = predicted_degs.intersection(gmt_gold)
    jaccard = len(intersection) / len(predicted_degs.union(gmt_gold))
    
    print(f"[Bench] Intersection: {intersection}")
    print(f"[Bench] Jaccard Similarity: {jaccard:.4f}")
    
    if jaccard > 0.1: # Improved from 0.0
        print("[Bench] Result: SIGNIFICANT CONCORDANCE (Sprint 2/4 Active)")
    else:
        print("[Bench] Result: LOW CONCORDANCE")

if __name__ == "__main__":
    test_gmt_bench()
