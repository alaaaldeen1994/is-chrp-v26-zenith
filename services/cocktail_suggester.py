# services/cocktail_suggester.py
from typing import List, Dict, Any

class CocktailSuggester:
    """
    Suggests alternative transcription factors if a cocktail is blocked.
    """
    
    # Map of target cell types to their known transcription factor networks
    FACTOR_NETWORKS = {
        "Cardiomyocyte": {
            "primary": ["GATA4", "MEF2C", "TBX5"],  # GMT (Known arrhythmia risk)
            "alternatives": [
                ["GATA4", "MESP1", "MYOCD"],         # Alternative 1: Myocd-based
                ["NKX2-5", "ISL1", "BMP2"],          # Alternative 2: Developmental pathway
                ["GATA4", "TBX5", "ESRRB"]           # Alternative 3: Esrrb-enhanced
            ]
        },
        "Neuron": {
            "primary": ["ASCL1", "BRN2", "MYT1L"],
            "alternatives": [
                ["NGN2", "ISL1", "PHOX2B"],
                ["ASCL1", "LHX3", "ISL1"]
            ]
        }
    }

    def __init__(self, perturbation_engine, substrate_service):
        self.perturbation_engine = perturbation_engine
        self.substrate = substrate_service.substrate

    def suggest_alternatives(self, blocked_factors: List[str], source_type: str, target_type: str) -> Dict[str, Any]:
        """
        Tests alternative factor combinations to find a SAFE path to the target.
        """
        print(f"[CocktailSuggester] Finding alternatives to {blocked_factors}...")
        
        network = self.FACTOR_NETWORKS.get(target_type, {})
        alternatives = network.get("alternatives", [])
        
        safe_alternatives = []
        
        for alt_cocktail in alternatives:
            # Run perturbation with the alternative cocktail
            result = self.perturbation_engine.predict_factor_effect(
                factors=alt_cocktail,
                source_type=source_type,
                target_type=target_type,
                dose=1.0
            )
            
            safety = result.get("arrhythmia_safety", {})
            classification = safety.get("classification", "BLOCKED")
            
            if classification == "SAFE":
                safe_alternatives.append({
                    "factors": alt_cocktail,
                    "safety_audit": safety,
                    "latent_displacement": result.get("latent_displacement", 0)
                })
                print(f"  -> SAFE alternative found: {alt_cocktail}")
                
        return {
            "status": "SUCCESS" if safe_alternatives else "NO_SAFE_ALTERNATIVES",
            "original_cocktail": blocked_factors,
            "safe_alternatives": safe_alternatives
        }
