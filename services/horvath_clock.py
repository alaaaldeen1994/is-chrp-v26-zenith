import os
import json
import numpy as np
from typing import Dict, Any

class HorvathClockService:
    """
    Epigenetic Clock Service implementing Horvath's 353-CpG methylation age predictor.
    Loads regression coefficients and computes biological age from CpG methylation levels.
    """
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        coef_path = os.path.join(base_dir, "models", "horvath_clock_coef.json")
        
        # Load probe map and coefficients
        if os.path.exists(coef_path):
            with open(coef_path, "r") as f:
                data = json.load(f)
                self.intercept = data.get("intercept", 0.696)
                self.coefficients = data.get("coefficients", {})
            print(f"[HorvathClockService] Loaded {len(self.coefficients)} coefficients successfully.")
        else:
            # Fallback model in case of missing model files
            print("[HorvathClockService] Warning: Coefficients file not found. Running baseline fallback.")
            self.intercept = 0.696
            self.coefficients = {f"cg{i:08}": 0.05 for i in range(353)}

    def calculate_age(self, methylation_matrix: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates biological age based on CpG beta-value maps (probe -> methylation level).
        If a probe is missing from the input matrix, a baseline beta-value of 0.5 is substituted.
        """
        linear_sum = self.intercept
        probes_used = 0
        missing_probes = 0
        
        for probe, coef in self.coefficients.items():
            # Beta values range from 0.0 (unmethylated) to 1.0 (fully methylated)
            if probe in methylation_matrix:
                beta = float(methylation_matrix[probe])
                # Bound beta value between 0.0 and 1.0
                beta = max(0.0, min(1.0, beta))
                probes_used += 1
            else:
                beta = 0.5  # Neutral default baseline value
                missing_probes += 1
                
            linear_sum += coef * beta
            
        # Horvath's age transformation logic:
        # Age is transformed log-linearly relative to adult age threshold (20 years)
        # Adult age mapping:
        # F(age) = log(age + 1) - log(21) if age < 20
        # F(age) = (age - 20) / 21 if age >= 20
        #
        # Inverse transform:
        # If F_age < 0: age = exp(F_age) * 21 - 1
        # If F_age >= 0: age = F_age * 21 + 20
        
        if linear_sum < 0:
            predicted_age = np.exp(linear_sum) * 21.0 - 1.0
        else:
            predicted_age = linear_sum * 21.0 + 20.0
            
        # Bound age between 0.0 and 120.0
        predicted_age = float(max(0.0, min(120.0, predicted_age)))
        
        return {
            "predicted_biological_age": round(predicted_age, 2),
            "probes_matched": probes_used,
            "probes_defaulted": missing_probes,
            "total_clock_probes": len(self.coefficients),
            "concordance_score": round(probes_used / len(self.coefficients), 3)
        }

# === NEUROS-X Neural Age Clock integration ===
import logging
logger = logging.getLogger("horvath_clock")

class DualAgeReport:
    """Combined Horvath (epigenetic) + Neural (functional) age report."""

    @staticmethod
    async def assess(horvath_clock, methylation_betas, gene_expression, chronological_age=50.0):
        try:
            horvath_age = horvath_clock.predict(methylation_betas)
        except Exception as e:
            logger.warning(f"Horvath prediction failed: {e}")
            horvath_age = chronological_age

        try:
            from services.neural_age_clock import get_neural_clock
            from services.neuros_substrate_service import get_substrate_service
            svc = get_substrate_service()
            clock = get_neural_clock(substrate_service=svc)
            neural_result = await clock.predict_with_substrate(gene_expression, chronological_age)
            neural_age = neural_result["neural_age"]
            phi_hat = neural_result.get("phi_hat")
            confidence = neural_result.get("confidence", 0)
        except Exception as e:
            logger.warning(f"Neural prediction failed: {e}")
            neural_age = chronological_age
            phi_hat = None
            confidence = 0.0

        horvath_gap = horvath_age - chronological_age
        neural_gap = neural_age - chronological_age
        dual_gap = neural_age - horvath_age

        if abs(dual_gap) < 3.0:
            phenotype = "concordant"
            phenotype_desc = "Epigenetic and neural ages aligned."
        elif dual_gap > 3.0:
            phenotype = "neural_dominant"
            phenotype_desc = "Neural aging outpaces genomic."
        else:
            phenotype = "genomic_dominant"
            phenotype_desc = "Genomic aging outpaces neural."

        return {
            "horvath_age": float(horvath_age),
            "neural_age": float(neural_age),
            "chronological_age": float(chronological_age),
            "horvath_gap": float(horvath_gap),
            "neural_gap": float(neural_gap),
            "dual_gap": float(dual_gap),
            "phenotype": phenotype,
            "phenotype_description": phenotype_desc,
            "phi_hat": phi_hat,
            "neural_confidence": confidence,
            "summary": f"Dual-age: Horvath {horvath_age:.1f}y, Neural {neural_age:.1f}y, Chronological {chronological_age:.0f}. Phenotype: {phenotype}.",
        }
