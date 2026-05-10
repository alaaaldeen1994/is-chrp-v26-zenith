import numpy as np
import pandas as pd
import json
import os
import torch
from typing import Dict, List, Optional, Any

# =================================================================
# CANONICAL DRUG-TARGET REPOSITORY (v27 Expert)
# Mapped mechanistic targets for regenerative medicine
# =================================================================

DRUG_DATABASE = {
    "CHIR99021": {
        "class": "GSK3 Inhibitor",
        "primary_target": "GSK3B",
        "mechanistic_signatures": ["CTNNB1", "MYC", "AXIN2", "LEF1"],
        "effect": "ACTIVATE_WNT",
        "potency": 0.85
    },
    "SB431542": {
        "class": "TGF-beta Inhibitor",
        "primary_target": "TGFBR1",
        "mechanistic_signatures": ["SMAD2", "SMAD3", "COL1A1", "POSTN", "ACTA2"],
        "effect": "INHIBIT_TGFB",
        "potency": 0.92
    },
    "XAV939": {
        "class": "Wnt Inhibitor",
        "primary_target": "TNKS1",
        "mechanistic_signatures": ["CTNNB1", "AXIN2", "MYC"],
        "effect": "INHIBIT_WNT",
        "potency": 0.78
    },
    "VPA": {
        "class": "HDAC Inhibitor",
        "primary_target": "HDAC1",
        "mechanistic_signatures": ["CDKN1A", "CDKN2A", "GATA4", "MEF2C"],
        "effect": "EPIGENETIC_PLASTICITY",
        "potency": 0.65
    },
    "BPIPP": {
        "class": "PKC Activator",
        "primary_target": "PRKCA",
        "mechanistic_signatures": ["FOS", "JUN", "EGR1"],
        "effect": "MAPK_SIGNALING",
        "potency": 0.70
    },
    "PD0325901": {
        "class": "MEK Inhibitor",
        "primary_target": "MAP2K1",
        "mechanistic_signatures": ["ELK1", "FOS", "SPRTY2"],
        "effect": "INHIBIT_MAPK",
        "potency": 0.88
    }
}

class DrugEngine:
    """
    Pharmacology extension for Zenith.
    Bridges the gap between chemical space and the scVI genomic manifold.
    """
    
    def __init__(self, engine: Any):
        self.pe = engine # PerturbationEngine instance
        self.db = DRUG_DATABASE
        
    def predict_drug_effect(self, drug_name: str, concentration: float = 1.0) -> Dict:
        """
        Predicts the transcriptomic shift caused by a small molecule.
        1. Find mechanistic targets
        2. Perturb gene space
        3. Re-encode to latent space to find the 'Drug Displacement Vector'
        """
        drug_name = drug_name.upper()
        if drug_name not in self.db:
            return {"error": f"Drug {drug_name} not found in database"}
            
        drug_info = self.db[drug_name]
        targets = drug_info["mechanistic_signatures"]
        potency = drug_info["potency"] * concentration
        
        # We start from a neutral state (Fibroblast default)
        source_type = "Fibroblast"
        if source_type not in self.pe.centroids:
            return {"error": "Engine centroids not loaded"}
            
        z_start = self.pe.centroids[source_type]
        
        # 1. Decode to gene space
        with torch.no_grad():
            gen_out = self.pe.model.module.generative(
                torch.tensor(z_start, dtype=torch.float32).unsqueeze(0),
                torch.log(torch.tensor([[1e4]])),
                batch_index=torch.zeros(1, 1, dtype=torch.long)
            )
            expr = gen_out["px"].mean.numpy().flatten()
            
        # 2. Apply chemical perturbation
        for t in targets:
            if t in self.pe.gene_to_idx:
                idx = self.pe.gene_to_idx[t]
                if drug_info["effect"].startswith("INHIBIT"):
                    expr[idx] *= (1.0 - potency)
                else:
                    expr[idx] += (potency * 2.0) # Heuristic activation
                    
        # 3. Re-encode to find the drug-induced latent position
        x_input = torch.tensor(expr[:4000], dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            encoder_out = self.pe.model.module.z_encoder(x_input, torch.zeros(1, 1, dtype=torch.long))
            z_drug = encoder_out[0].loc.numpy().flatten()
            
        # 4. Calculate displacement vector
        delta_z = z_drug - z_start
        
        return {
            "drug": drug_name,
            "class": drug_info["class"],
            "primary_target": drug_info["primary_target"],
            "delta_z": delta_z.tolist(),
            "displacement_magnitude": float(np.linalg.norm(delta_z)),
            "method": "pharmacokinetic_latent_projection",
            "provenance": "PREDICTED (Targeted Mechanism)"
        }

    def simulate_hybrid_therapy(self, factors: List[str], drugs: List[str], source: str = "Fibroblast") -> Dict:
        """
        Synergy Simulator: Combines TF overexpression with small molecule modulation.
        """
        # Get factor effect
        factor_res = self.pe.predict_factor_effect(factors, source_type=source)
        z_tf = np.array(factor_res["z"])
        
        # Add drug displacements
        z_hybrid = z_tf.copy()
        applied_drugs = []
        
        for d in drugs:
            d_res = self.predict_drug_effect(d)
            if "error" not in d_res:
                z_hybrid += np.array(d_res["delta_z"])
                applied_drugs.append(d)
                
        # Audit the final hybrid state
        # Find nearest centroid in scVI space
        nearest_type, dist = self.pe._nearest_centroid(z_hybrid)
        
        return {
            "source": source,
            "tfs": factors,
            "drugs": applied_drugs,
            "z_hybrid": z_hybrid.tolist(),
            "final_cell_fate": nearest_type,
            "fate_confidence": round(float(1.0 / (1.0 + dist)), 4),
            "synergy_bonus": len(applied_drugs) * 0.12 # Heuristic synergy
        }

# =================================================================
# API BRIDGE MOCK
# =================================================================
if __name__ == "__main__":
    from perturbation_engine import PerturbationEngine
    print("[DrugEngine] Initializing...")
    pe = PerturbationEngine()
    pe.initialize()
    
    de = DrugEngine(pe)
    print("[DrugEngine] Simulating GMT + SB431542 + CHIR99021...")
    
    hybrid = de.simulate_hybrid_therapy(
        factors=["GATA4", "MEF2C", "TBX5"],
        drugs=["SB431542", "CHIR99021"]
    )
    
    print(f"[Result] Predicted Fate: {hybrid['final_cell_fate']}")
    print(f"[Result] Confidence: {hybrid['fate_confidence']}")
    
    with open("DRUG_TEST_RESULTS.json", "w") as f:
        json.dump(hybrid, f, indent=4)
