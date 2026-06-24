import numpy as np
from typing import Dict, Any

class LNPOptimizerService:
    """
    Microservice for mRNA-LNP (Lipid Nanoparticle) delivery and organ tropism optimization.
    Evaluates lipid molar compositions to maximize cardiac target specificity and
    minimize liver sequestration.
    
    Updated to resolve the physiological "Liver Barrier" gap:
    - Caps passive lipid-ratio cardiac targeting at <10%.
    - Implements ApoE-mediated liver sequestration LDLR clearance penalty.
    - Requires active ligand conjugation (e.g. peptide/antibody) to unlock >70% cardiac selectivity.
    """
    
    def __init__(self):
        # Baseline coefficients for tissue bio-distribution modeling
        # Corresponds to clinical screening assays for nanoparticle tracking
        self.biodistribution_weights = {
            "ionizable": {"heart": 1.75, "liver": 0.40, "spleen": 0.90},
            "helper": {"heart": 0.50, "liver": 1.10, "spleen": 0.70},
            "cholesterol": {"heart": 0.80, "liver": 0.90, "spleen": 0.60},
            "peg": {"heart": -2.20, "liver": -0.80, "spleen": -1.50}  # PEGylation shields tropism
        }

    def evaluate_formulation(self, molar_ratios: Dict[str, float], np_ratio: float) -> Dict[str, Any]:
        """
        Evaluates the physical encapsulation and tissue tropism of a target formulation.
        
        Inputs:
        - molar_ratios: Dictionary of lipid molar percentages (ionizable, cholesterol, helper, peg)
          Can include "active_targeting" (1.0 for active ligand conjugation, 0.0 for passive)
        - np_ratio: Nitrogen-to-Phosphate ratio
        """
        # Retrieve molar values
        ion = max(0.0, float(molar_ratios.get("ionizable", 50.0)))
        chol = max(0.0, float(molar_ratios.get("cholesterol", 38.5)))
        helper = max(0.0, float(molar_ratios.get("helper", 10.0)))
        peg = max(0.0, float(molar_ratios.get("peg", 1.5)))
        
        # Check active targeting conjugation parameter
        active_targeting = float(molar_ratios.get("active_targeting", 0.0)) > 0.5
        
        # Ensure molar ratios sum to 100% (normalize if not)
        sum_molar = ion + chol + helper + peg
        if sum_molar <= 0.0:
            ion, chol, helper, peg = 50.0, 38.5, 10.0, 1.5
            sum_molar = 100.0
            
        f_ion = ion / sum_molar
        f_chol = chol / sum_molar
        f_helper = helper / sum_molar
        f_peg = peg / sum_molar
        
        # 1. Encapsulation Efficiency (EE%) model
        # Higher N/P ratios improve complexation efficiency but can introduce cell toxicity
        # Modelled with a logarithmic saturation: EE = 100 * (1 - e^(-0.48 * NP))
        encapsulation_eff = 100.0 * (1.0 - np.exp(-0.48 * max(0.1, np_ratio)))
        encapsulation_eff = float(np.round(min(99.9, max(5.0, encapsulation_eff)), 2))
        
        # 2. Tissue tropism score calculations with physiological liver barriers
        if not active_targeting:
            # Passive Targeting Mode: ApoE adsorbs to LNP forming a protein corona.
            # Hepatocytes clear nanoparticles via LDLR pathway through 100-150nm sinusoidal fenestrations.
            # Myocardial capillaries possess a continuous, non-fenestrated endothelium blocking passive uptake.
            
            # Liver sequestration is extremely high (typically 85% to 95%)
            charge_factor = 0.05 * max(0.0, np_ratio - 6.0)
            peg_shielding = 0.10 * np.tanh(peg / 1.5)
            liver_index = 0.88 + charge_factor - peg_shielding
            liver_index = float(np.round(max(0.75, min(0.98, liver_index)), 3))
            
            # Passive heart targeting is capped at 10%
            heart_index = float(np.round(0.02 + 0.08 * (1.0 - liver_index), 3))
            
            # Spleen and other tissues take up the rest
            spleen_index = float(np.round(1.0 - liver_index - heart_index, 3))
            
            delivery_status = "SUBOPTIMAL_LIVER_TRAPPED"
            mechanism_note = "Passive delivery trapped in liver. ApoE corona adsorption triggers hepatocyte LDLR endocytosis. Myocardial continuous endothelium prevents passive entry."
            
        else:
            # Active Targeting Mode: Active ligand conjugation (e.g. anti-CD31 or cardiac-specific peptide)
            # facilitates active receptor-mediated transcytosis across the continuous myocardial endothelium.
            
            # Specific organ targeting coefficients multiplied by normalized molar fractions
            heart_raw = (f_ion * 4.5) + (f_chol * 1.5) + (f_helper * 0.8) - (f_peg * 15.0)
            liver_raw = (f_ion * 1.5) + (f_chol * 0.5) + (f_helper * 0.8) - (f_peg * 2.0)
            
            # Apply N/P ratio influence (higher charge increases liver/spleen clearance)
            heart_raw -= 0.04 * max(0.0, np_ratio - 6.0)
            liver_raw += 0.08 * max(0.0, np_ratio - 6.0)
            
            # Sigmoidal normalization of tropism index
            heart_tropism = 1.0 / (1.0 + np.exp(-heart_raw))
            liver_tropism = 1.0 / (1.0 + np.exp(-liver_raw))
            
            # Normalize to sum to 1.0 (with a minor spleen fraction)
            total_trop = heart_tropism + liver_tropism + 0.1
            heart_index = float(np.round(heart_tropism / total_trop, 3))
            liver_index = float(np.round(liver_tropism / total_trop, 3))
            
            delivery_status = "OPTIMIZED" if heart_index >= 0.70 else "MODERATE_TROPISM"
            mechanism_note = "Active ligand conjugation bypasses the liver barrier, enabling receptor-mediated endothelial transcytosis into cardiac tissue."

        # Determine overall optimization status bounds
        status = "SUBOPTIMAL"
        if encapsulation_eff >= 92.0 and heart_index >= 0.70:
            status = "OPTIMIZED_DELIVERY"
        elif encapsulation_eff >= 80.0 and heart_index >= 0.50:
            status = "MODERATE_DELIVERY"
        elif "LIVER_TRAPPED" in delivery_status:
            status = "LIVER_TRAPPED"
            
        return {
            "encapsulation_efficiency_percent": encapsulation_eff,
            "heart_selectivity_score": heart_index,
            "liver_sequestration_score": liver_index,
            "formulation_status": status,
            "delivery_mechanism": delivery_status,
            "mechanism_note": mechanism_note,
            "biophysical_metrics": {
                "zeta_potential_mv": float(np.round(15.2 + 2.1 * (np_ratio - 6.0), 2)),
                "particle_size_nm": float(np.round(85.0 + 120.0 * f_peg + 5.0 * np_ratio, 1))
            }
        }
