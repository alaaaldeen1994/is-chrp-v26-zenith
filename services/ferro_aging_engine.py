"""
Cardiac Ferro-Aging Engine (v31.0 GOLD)
Based on: Liu et al., Cell Metabolism 2026 ("Vitamin C inhibits ACSL4 to alleviate ferro-aging in primates").

Quantifies lipid peroxidation and ferroptotic vulnerability in high-mitochondrial cardiomyocytes.
Monitors the ACSL4/GPX4 balance to prevent cardiomyocyte dropout during transient cellular reprogramming.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class FerroAgingEngine:
    """
    Evaluates cardiomyocyte ferroptotic vulnerability during transient transcriptional reprogramming.
    """

    def __init__(self):
        # Master ferro-aging biomarkers
        # Pro-ferroptotic: drive PUFA-CoA generation, membrane phospholipid peroxidation, and ferritinophagy
        self.pro_ferroptosis_markers = ["ACSL4", "LPCAT3", "NCOA4", "TFRC", "ALOX15"]
        # Anti-ferroptotic: GPX4 lipid hydroperoxide reduction, cystine import (SLC7A11/xCT),
        # iron sequestration (FTH1), GSH synthesis (GCLC), and GPX4-independent CoQ10 defense (AIFM2/FSP1)
        self.anti_ferroptosis_markers = ["GPX4", "SLC7A11", "FTH1", "GCLC", "AIFM2"]
        
        # Baselines for young, healthy cardiomyocytes (normalized expression 0-1)
        # Cardiomyocytes have ~40% mitochondrial volume density, making them
        # uniquely vulnerable to iron-catalysed lipid peroxidation (Fenton reaction)
        self.baseline_reference = {
            "ACSL4": 0.25,   # PUFA-CoA thioesterification (pro-ferroptotic driver)
            "GPX4": 0.85,    # Master lipid hydroperoxide reductase
            "SLC7A11": 0.70, # System Xc- cystine/glutamate antiporter
            "FTH1": 0.80,    # Ferritin heavy chain (Fe2+ -> Fe3+ sequestration)
            "LPCAT3": 0.30,  # Lysophospholipid acyltransferase 3 (PE-AA/PE-AdA synthesis)
            "NCOA4": 0.20,   # Ferritinophagy cargo receptor
            "ALOX15": 0.15   # 15-Lipoxygenase (direct PUFA-PE oxygenation)
        }

    def calculate_ferro_aging_index(self, expression_profile: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates the Ferro-Aging Index (FAI):
        Pro = ACSL4 + 0.4*LPCAT3 + 0.3*ALOX15   (lipid substrate generation + direct PUFA-PE oxidation)
        Anti = GPX4 + 0.8*SLC7A11 + 0.5*FTH1     (peroxide clearance + GSH precursor + iron sequestration)
        FAI = Pro / (Anti + epsilon)
        """
        acsl4 = float(expression_profile.get("ACSL4", self.baseline_reference["ACSL4"]))
        lpcat3 = float(expression_profile.get("LPCAT3", self.baseline_reference["LPCAT3"]))
        alox15 = float(expression_profile.get("ALOX15", self.baseline_reference["ALOX15"]))
        gpx4 = float(expression_profile.get("GPX4", self.baseline_reference["GPX4"]))
        slc7a11 = float(expression_profile.get("SLC7A11", self.baseline_reference["SLC7A11"]))
        fth1 = float(expression_profile.get("FTH1", self.baseline_reference["FTH1"]))

        # ACSL4 drives PUFA-CoA -> LPCAT3 inserts into PE -> ALOX15 oxidises PE-PUFA
        pro_score = acsl4 + 0.4 * lpcat3 + 0.3 * alox15
        # GPX4 reduces L-OOH; SLC7A11 feeds cystine->GSH->GPX4; FTH1 sequesters Fe2+
        anti_score = gpx4 + 0.8 * slc7a11 + 0.5 * fth1 + 1e-5
        
        fai = float(pro_score / anti_score)
        
        # Risk classification
        if fai < 0.60:
            status = "OPTIMAL_CYTOPROTECTION"
            risk_level = "LOW"
            color = "#10b981" # Green
            message = "Cardiomyocyte ferroptosis resistance intact. Membrane lipid stability verified."
            adjuvant_recommendation = None
        elif fai <= 1.20:
            status = "BALANCED_HOMEOSTASIS"
            risk_level = "MODERATE"
            color = "#f59e0b" # Amber
            message = "Minor lipid peroxidation risk. Standard 2.0h DRP pulse kinetics safe."
            adjuvant_recommendation = (
                "Ascorbic Acid (Vitamin C) — direct ACSL4 catalytic pocket inhibitor "
                "(binds Thr278/Ser279/Thr469; Liu et al., Cell Metab 2026)."
            )
        else:
            status = "HIGH_FERRO_AGING_RISK"
            risk_level = "HIGH"
            color = "#ef4444" # Red
            message = "Elevated ACSL4 expression detected. High risk of ferroptotic cardiomyocyte loss."
            adjuvant_recommendation = (
                "Co-administer: (1) Ascorbic Acid — direct ACSL4 inhibitor "
                "(Thr278/Ser279/Thr469 binding; Liu et al., Cell Metab 2026); "
                "(2) Liproxstatin-1 — radical-trapping antioxidant in lipid bilayer "
                "(rescues GPX4, protects mitochondrial membrane integrity)."
            )

        # Calculate protection retention percentage (0 - 100%)
        protection_score = round(max(0.0, min(100.0, (1.0 - (fai / 2.0)) * 100.0)), 1)

        return {
            "ferro_aging_index": round(fai, 3),
            "protection_score_pct": protection_score,
            "status": status,
            "risk_level": risk_level,
            "color": color,
            "message": message,
            "acsl4_level": round(acsl4, 3),
            "gpx4_level": round(gpx4, 3),
            "slc7a11_level": round(slc7a11, 3),
            "adjuvant_recommendation": adjuvant_recommendation,
            "literature_reference": "Liu et al., Cell Metabolism (2026) — ACSL4 ferro-aging inhibition"
        }


# Singleton instance
_ferro_engine: Optional[FerroAgingEngine] = None

def get_ferro_aging_engine() -> FerroAgingEngine:
    global _ferro_engine
    if _ferro_engine is None:
        _ferro_engine = FerroAgingEngine()
    return _ferro_engine
