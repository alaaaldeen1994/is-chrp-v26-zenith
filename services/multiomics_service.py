import numpy as np
from typing import Dict, Any, List

class MultiOmicsPredictorService:
    """
    Microservice for zero-shot transcriptomic and cellular state perturbation forecasting.
    Emulates biological foundation models leveraging gene regulatory networks and pioneer factor dynamics:
    - Pioneer factor partial reprogramming (OSK vs. c-Myc oncogenic risk).
    - Chemical reprogramming dynamics (CHIR99021, RepSox, Forskolin).
    - Sirtuin network regulation (SIRT1/5/6).
    - Syncytial Safety Index (GJA1/Connexin 43 conduction risk).
    """
    
    def __init__(self):
        # Human primary ventricular cell state baseline checkpoints (10 key genes)
        self.baseline_expressions = {
            "TNNT2": 2.50,  # Cardiac Troponin T2 (sarcomeric structural marker)
            "MYH6": 1.80,   # Alpha-myosin heavy chain (contractility engine)
            "ACTC1": 3.10,  # Alpha-cardiac actin (thin filament structural core)
            "NPPA": 0.90,   # Natriuretic peptide A (atrial/ventricular stress indicator)
            "SIRT1": 1.20,  # Sirtuin 1 (genomic silencer, vascular integrity)
            "SIRT5": 0.80,  # Sirtuin 5 (cardiac anti-fibrosis, pressure overload protector)
            "SIRT6": 1.00,  # Sirtuin 6 (DNA double-strand break repair)
            "GJA1": 2.20,   # Connexin 43 (gap junction coupling)
            "KCNJ2": 1.50,  # Kir2.1 (IK1 inward rectifier potassium channel)
            "SCN5A": 1.70   # Nav1.5 (INa cardiac sodium channel)
        }
        
        # Pioneer factor transcriptional target mappings and regulatory coefficients
        # Based on JASPAR database position weight matrix (PWM) motif occupancy
        self.factor_regulatory_weights = {
            "GATA4": {"TNNT2": 1.85, "MYH6": 1.40, "ACTC1": 1.65, "NPPA": 1.10, "SIRT5": 0.40, "GJA1": 0.50, "KCNJ2": 0.30, "SCN5A": 0.25},
            "MEF2C": {"TNNT2": 1.50, "MYH6": 1.95, "ACTC1": 1.10, "NPPA": 0.80, "SIRT5": 0.30, "GJA1": 0.60, "KCNJ2": 0.45, "SCN5A": 0.30},
            "TBX5":  {"TNNT2": 1.35, "MYH6": 1.10, "ACTC1": 1.90, "NPPA": 1.45, "SIRT5": 0.25, "GJA1": 0.40, "KCNJ2": 0.20, "SCN5A": 0.40},
            "NKX2-5":{"TNNT2": 1.60, "MYH6": 1.25, "ACTC1": 1.30, "NPPA": 1.75, "SIRT5": 0.50, "GJA1": 0.70, "KCNJ2": 0.35, "SCN5A": 0.35},
            "OCT4":  {"SIRT1": 1.70, "SIRT6": 1.50, "GJA1": 0.40, "TNNT2": 0.10, "MYH6": 0.10, "ACTC1": 0.10, "NPPA": -0.30, "KCNJ2": 0.10, "SCN5A": 0.10},
            "SOX2":  {"SIRT1": 1.55, "SIRT6": 1.65, "GJA1": 0.35, "TNNT2": 0.05, "MYH6": 0.05, "ACTC1": 0.05, "NPPA": -0.25, "KCNJ2": 0.05, "SCN5A": 0.05},
            "KLF4":  {"SIRT1": 1.40, "SIRT6": 1.30, "GJA1": 0.50, "TNNT2": 0.08, "MYH6": 0.08, "ACTC1": 0.08, "NPPA": -0.20, "KCNJ2": 0.15, "SCN5A": 0.15},
            "MYC":   {"TNNT2": -0.80, "MYH6": -0.60, "ACTC1": -0.50, "NPPA": 2.10, "SIRT1": -0.90, "SIRT6": -1.10, "GJA1": -1.50, "KCNJ2": -1.20, "SCN5A": -1.10},
            "SNAI1": {"TNNT2": -1.20, "MYH6": -1.10, "ACTC1": -0.95, "NPPA": 1.50, "SIRT1": -0.50, "GJA1": -1.00, "KCNJ2": -0.80, "SCN5A": -0.80}
        }

    def predict_perturbation_trajectory(self, baseline_cell_type: str, factors: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates cell-type-specific developmental transition trajectories under factor cocktails.
        Mechanistic simulation incorporating pioneer transcription factor dynamics and gene regulatory networks.
        """
        chir = max(0.0, float(factors.get("CHIR99021", 0.0)))
        repsox = max(0.0, float(factors.get("RepSox", 0.0)))
        forskolin = max(0.0, float(factors.get("Forskolin", 0.0)))
        nmn = max(0.0, float(factors.get("NMN", 0.0)))

        # Translate chemical inputs to effective pioneer factor transcription levels
        gata4_eff = max(0.0, float(factors.get("GATA4", 0.0))) + 0.65 * chir
        mef2c_eff = max(0.0, float(factors.get("MEF2C", 0.0))) + 0.40 * forskolin
        tbx5_eff  = max(0.0, float(factors.get("TBX5", 0.0)))
        nkx25_eff = max(0.0, float(factors.get("NKX2-5", 0.0))) + 0.30 * chir

        oct4_eff  = max(0.0, float(factors.get("OCT4", 0.0))) + 0.50 * chir + 0.30 * repsox
        sox2_eff  = max(0.0, float(factors.get("SOX2", 0.0))) + 0.70 * repsox
        klf4_eff  = max(0.0, float(factors.get("KLF4", 0.0))) + 0.45 * repsox + 0.25 * forskolin

        myc_eff   = max(0.0, float(factors.get("MYC", 0.0)))
        snai1_eff = max(0.0, float(factors.get("SNAI1", 0.0)))
        if repsox > 0.0:
            snai1_eff = max(0.0, snai1_eff - 0.80 * repsox)

        effective_factors = {
            "GATA4": gata4_eff, "MEF2C": mef2c_eff, "TBX5": tbx5_eff, "NKX2-5": nkx25_eff,
            "OCT4": oct4_eff, "SOX2": sox2_eff, "KLF4": klf4_eff, "MYC": myc_eff, "SNAI1": snai1_eff
        }

        reprogramming_tf_sum = oct4_eff + sox2_eff + klf4_eff
        structural_tf_sum = gata4_eff + mef2c_eff + tbx5_eff + nkx25_eff
        risk_tf_sum = myc_eff + snai1_eff

        # 1. Dynamic target gene expression modeling with regulatory weights
        expression_profiles = {}
        for gene, base_val in self.baseline_expressions.items():
            acc_val = base_val
            for tf, dosage in effective_factors.items():
                if tf in self.factor_regulatory_weights:
                    weight = self.factor_regulatory_weights[tf].get(gene, 0.0)
                    acc_val += weight * float(dosage)

            # Apply cell-type cell-state corrections
            if baseline_cell_type == "fibroblast":
                acc_val = acc_val * 1.15 if (structural_tf_sum + reprogramming_tf_sum) > 2.0 else acc_val * 0.70
            elif baseline_cell_type == "macrophage":
                acc_val = acc_val * 0.60

            expression_profiles[gene] = float(np.round(max(0.0, acc_val), 2))

        s1 = expression_profiles["SIRT1"]
        s5 = expression_profiles["SIRT5"]
        s6 = expression_profiles["SIRT6"]
        gja1 = expression_profiles["GJA1"]
        kcnj2 = expression_profiles["KCNJ2"]
        scn5a = expression_profiles["SCN5A"]

        # 2. Sirtuin Activity Index
        sirt_sum = (0.45 * s1) + (0.35 * s5) + (0.20 * s6) + 0.10
        sirt_activity_index = float(np.round(sirt_sum / 3.0, 3))

        # 3. Syncytial Safety Index (Arrhythmia Risk)
        syncytial_safety = 1.0 / (1.0 + np.exp(-2.5 * (gja1 - 1.2) - 1.5 * (kcnj2 - 0.8) - 1.5 * (scn5a - 0.9)))
        syncytial_safety = float(np.round(max(0.0, min(1.0, syncytial_safety)), 3))

        # 4. Transcriptomic state stability index calculation
        dose_penalty = 0.02 * max(0.0, (structural_tf_sum + reprogramming_tf_sum) - 5.5)
        risk_penalty = 0.35 * np.tanh(risk_tf_sum / 2.0)
        stability = 0.99 - dose_penalty - risk_penalty

        stability = float(np.round(stability, 4))
        stability = max(0.100, min(0.999, stability))

        chromatin_status = "RESTRICTED"
        if oct4_eff > 0.8 and sox2_eff > 0.8:
            chromatin_status = "OPEN_ACCESSIBLE_REPROGRAMMED"
        elif (structural_tf_sum + reprogramming_tf_sum) > 2.5:
            chromatin_status = "PARTIALLY_ACCESSIBLE"

        result = {
            "transcriptomic_stability": stability,
            "sirtuin_activity_index": sirt_activity_index,
            "syncytial_safety_index": syncytial_safety,
            "expression_profiles": expression_profiles,
            "chromatin_state": chromatin_status,
            "status": "CONVERGED" if stability > 0.80 else "METASTABLE_DRIFT"
        }

        return result
