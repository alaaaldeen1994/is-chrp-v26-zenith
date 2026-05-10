import numpy as np
import pandas as pd
import json
import os
from typing import Dict, List, Set, Any
from sklearn.metrics import jaccard_score

# =================================================================
# CANONICAL LITERATURE REPROGRAMMING REPOSITORY (v27 Expert)
# Curated from Nature, Cell, and Science (2010-2024)
# =================================================================

LITERATURE_DATA = {
    "CARDIAC_GMT": {
        "paper": "Ieda et al., Cell 2010",
        "factors": ["GATA4", "MEF2C", "TBX5"],
        "source": "Fibroblast",
        "target": "Cardiomyocyte",
        "up_genes": [
            "TNNT2", "MYH7", "NPPA", "ACTN2", "GATA4", "MEF2C", "TBX5", 
            "RYR2", "PLN", "MYL2", "MYL7", "TTN", "SLC8A1", "HCN4", 
            "NKX2-5", "MYH6", "TNNI3", "HAND2", "ISL1", "ACTC1"
        ],
        "down_genes": ["COL1A1", "COL3A1", "POSTN", "DDR2", "FAP", "THY1", "VIM"]
    },
    "CARDIAC_GHMT": {
        "paper": "Song et al., Nature 2012",
        "factors": ["GATA4", "HAND2", "MEF2C", "TBX5"],
        "source": "Fibroblast",
        "target": "Cardiomyocyte",
        "up_genes": [
            "TNNT2", "MYH7", "NPPA", "MYH6", "TNNI3", "ANKRD1", "MYL2", 
            "GJA1", "SCN5A", "KCNJ2", "CACNA1C", "GATA4", "MEF2C", "TBX5", "HAND2"
        ],
        "down_genes": ["COL1A1", "POSTN", "SNAI1", "SNAI2", "TWIST1"]
    },
    "NEURONAL_BAM": {
        "paper": "Vierbuchen et al., Nature 2010",
        "factors": ["ASCL1", "BRN2", "MYT1L"],
        "source": "Fibroblast",
        "target": "Neuron",
        "up_genes": [
            "MAP2", "TUBB3", "NCAM1", "RBFOX3", "SNAP25", "SYP", "SYN1", 
            "DLG4", "GRIN1", "GRIA2", "GAD1", "SLC17A7", "ASCL1", "POU3F2", "MYT1L"
        ],
        "down_genes": ["COL1A1", "VIM", "ACTA2"]
    },
    "HEPATOCYTE_HSF": {
        "paper": "Huang et al., Nature 2011",
        "factors": ["HNF4A", "FOXA1", "FOXA2", "FOXA3"],
        "source": "Fibroblast",
        "target": "Hepatocyte",
        "up_genes": [
            "ALB", "AFP", "TTR", "APOA1", "APOA2", "F9", "SERPINA1", 
            "HNF4A", "FOXA1", "FOXA2", "FOXA3", "KRT8", "KRT18"
        ],
        "down_genes": ["COL1A1", "COL3A1"]
    },
    "IPSC_YAMANAKA": {
        "paper": "Takahashi & Yamanaka, Cell 2006",
        "factors": ["POU5F1", "SOX2", "KLF4", "MYC"],
        "source": "Fibroblast",
        "target": "iPSC",
        "up_genes": [
            "POU5F1", "SOX2", "NANOG", "KLF4", "MYC", "LIN28A", "DPPA4", 
            "GDF3", "REX1", "DNMT3B", "TERT", "SALL4", "UTF1"
        ],
        "down_genes": ["COL1A1", "VIM", "POSTN", "THY1"]
    }
}

class LiteratureBenchmark:
    """
    Expert-level validation suite for cellular reprogramming.
    Compares scVI predictions against the cumulative knowledge of 15 years of literature.
    """
    
    def __init__(self, engine_path: str = None):
        self.engine = None
        if engine_path:
            from perturbation_engine import PerturbationEngine
            self.engine = PerturbationEngine()
            self.engine.initialize()
            
    def score_prediction(self, protocol_key: str, prediction: Dict) -> Dict:
        """
        Calculates concordance between a Zenith prediction and literature gold standard.
        """
        if protocol_key not in LITERATURE_DATA:
            return {"error": f"Protocol {protocol_key} not in database"}
            
        gold = LITERATURE_DATA[protocol_key]
        # v27 Fix: Support both dict and list for deg_up
        raw_up = prediction.get("deg_up", [])
        pred_up = set(raw_up.keys() if isinstance(raw_up, dict) else raw_up)
        
        # Calculate Jaccard for Up-regulated genes
        gold_up = set(gold["up_genes"])
        intersection = pred_up.intersection(gold_up)
        union = pred_up.union(gold_up)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Calculate Phenotypic Drift Score
        # How close did we get to the target centroid?
        target_name = gold["target"]
        dist_to_target = prediction.get("distance_to_target", 99.0)
        
        # Normalize distance (heuristic)
        fidelity = (jaccard * 0.7) + (max(0, 1 - (dist_to_target/10.0)) * 0.3)
        fidelity_percent = round(fidelity * 100, 2)
        
        return {
            "protocol": protocol_key,
            "paper": gold["paper"],
            "jaccard_similarity": round(jaccard, 4),
            "matching_markers": list(intersection),
            "missing_markers": list(gold_up - pred_up),
            "fidelity_score": fidelity_percent,
            "tier": self._get_tier(fidelity_percent),
            "status": "PASS" if fidelity_percent > 60 else "FAIL"
        }
        
    def _get_tier(self, score: float) -> str:
        if score > 85: return "PROFESSOR (Tier 1)"
        if score > 70: return "RESEARCHER (Tier 2)"
        if score > 50: return "STUDENT (Tier 3)"
        return "NON-CONCORDANT"

    def run_full_audit(self) -> Dict:
        """
        Audits all canonical protocols against the current PerturbationEngine.
        """
        if not self.engine:
            return {"error": "Engine not initialized"}
            
        results = {}
        for key, data in LITERATURE_DATA.items():
            print(f"[Audit] Testing Protocol: {key} ({data['paper']})...")
            # Predict
            pred = self.engine.predict_factor_effect(
                factors=data["factors"],
                source_type=data["source"],
                target_type=data["target"],
                dose=5.0 # Maximum expert-level strength
            )
            
            # Distance to target is missing from default return, calculate it
            if "z" in pred and data["target"] in self.engine.centroids:
                z_pred = np.array(pred["z"])
                z_target = self.engine.centroids[data["target"]]
                pred["distance_to_target"] = float(np.linalg.norm(z_pred - z_target))
            
            results[key] = self.score_prediction(key, pred)
            
        return results

    def generate_report(self, results: Dict) -> str:
        """
        Generates a markdown report of the audit.
        """
        report = "# Zenith v27: Literature Concordance Audit\n\n"
        report += "| Protocol | Paper | Jaccard | Fidelity | Tier | Status |\n"
        report += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        
        for key, res in results.items():
            report += f"| {key} | {res['paper']} | {res['jaccard_similarity']:.3f} | {res['fidelity_score']}% | {res['tier']} | {res['status']} |\n"
            
        return report

# =================================================================
# MAIN CLI
# =================================================================

if __name__ == "__main__":
    import time
    t0 = time.time()
    
    print("=========================================================")
    print(" ZENITH v27 LITERATURE CONCORDANCE BENCHMARK             ")
    print("=========================================================")
    
    benchmark = LiteratureBenchmark(engine_path="models/scvi_model_486k")
    results = benchmark.run_full_audit()
    
    report = benchmark.generate_report(results)
    with open("BENCHMARK_REPORT.md", "w") as f:
        f.write(report)
        
    print(f"\n[Done] Audit completed in {time.time()-t0:.2f}s")
    print("[Report] Saved to BENCHMARK_REPORT.md")
    
    # Print summary
    avg_fidelity = np.mean([r["fidelity_score"] for r in results.values()])
    print(f"[Summary] Global Fidelity Score: {avg_fidelity:.2f}%")
