"""Patch for services/horvath_clock.py — add NEUROS-X Neural Age companion.

This file shows EXACTLY what to add to your existing horvath_clock.py.
No need to rewrite the file — just add these lines.

=== EXISTING horvath_clock.py structure (you have this) ===

class HorvathClock:
    def predict(self, betas: dict) -> float:
        linear = 0.696 + sum(coef * betas[cpg] for cpg, coef in COEFFICIENTS.items())
        if linear < 0:
            age = math.exp(linear) * 21 - 1
        else:
            age = linear * 21 + 20
        return age

=== ADD THIS AT THE BOTTOM OF horvath_clock.py ===
"""

# ---------------------------------------------------------------------------
# ADD: Dual-age integration with NEUROS-X Neural Age Clock
# ---------------------------------------------------------------------------

# --- copy from here ---

import logging

logger = logging.getLogger("horvath_clock")


class DualAgeReport:
    """Combined Horvath (epigenetic) + Neural (functional) age report.

    Wraps both clocks and produces the dual-age phenotype — the unique
    marketing metric that no competitor offers.

    Usage:
        horvath = HorvathClock()
        report = await DualAgeReport.assess(
            horvath_clock=horvath,
            methylation_betas=beta_dict,
            gene_expression=expression_dict,  # from scVI decoder
            chronological_age=55,
        )
        print(report["summary"])
        # "Dual-age: Horvath 52.3y, Neural 61.2y, Chronological 55. Concordant."
    """

    @staticmethod
    async def assess(
        horvath_clock,
        methylation_betas: dict,
        gene_expression: dict,
        chronological_age: float = 50.0,
    ) -> dict:
        """Compute both ages and return the dual-age phenotype.

        Args:
            horvath_clock: an instance of HorvathClock
            methylation_betas: {cpg_id: beta_value} for 353-CpG Horvath
            gene_expression: {gene_symbol: level} from scVI decoder (4000 genes)
            chronological_age: donor age

        Returns:
            dict with horvath_age, neural_age, dual_gap, phenotype, summary
        """
        # 1. Horvath age (epigenetic)
        try:
            horvath_age = horvath_clock.predict(methylation_betas)
        except Exception as e:
            logger.warning(f"Horvath prediction failed: {e}")
            horvath_age = chronological_age

        # 2. Neural age (functional) — uses NEUROS-X substrate
        try:
            # lazy import to avoid circular dependency
            from services.neural_age_clock import get_neural_clock
            from services.neuros_substrate_service import get_substrate_service

            svc = get_substrate_service()
            clock = get_neural_clock(substrate_service=svc)
            neural_result = await clock.predict_with_substrate(
                gene_expression, chronological_age
            )
            neural_age = neural_result["neural_age"]
            phi_hat = neural_result.get("phi_hat")
            confidence = neural_result.get("confidence", 0)
        except Exception as e:
            logger.warning(f"Neural prediction failed: {e}")
            neural_age = chronological_age
            phi_hat = None
            confidence = 0.0

        # 3. Compute the dual-age phenotype
        horvath_gap = horvath_age - chronological_age
        neural_gap = neural_age - chronological_age
        dual_gap = neural_age - horvath_age

        if abs(dual_gap) < 3.0:
            phenotype = "concordant"
            phenotype_desc = "Epigenetic and neural ages aligned — uniform aging."
        elif dual_gap > 3.0:
            phenotype = "neural_dominant"
            phenotype_desc = "Neural aging outpaces genomic — autonomic decline."
        else:
            phenotype = "genomic_dominant"
            phenotype_desc = "Genomic aging outpaces neural — epigenetic drift."

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
            "summary": (
                f"Dual-age: Horvath {horvath_age:.1f}y, Neural {neural_age:.1f}y, "
                f"Chronological {chronological_age:.0f}. Phenotype: {phenotype}."
            ),
        }


# --- end copy ---


# ---------------------------------------------------------------------------
# ALSO ADD: a convenience endpoint wrapper for bridge_server.py
# ---------------------------------------------------------------------------

# In bridge_server.py, add this endpoint (after your existing Horvath endpoint):

"""
@app.post("/api/v1/horvath/dual-age")
async def dual_age_endpoint(request: Request):
    body = await request.json()
    from services.horvath_clock import HorvathClock, DualAgeReport
    horvath = HorvathClock()
    report = await DualAgeReport.assess(
        horvath_clock=horvath,
        methylation_betas=body["methylation_betas"],
        gene_expression=body["gene_expression"],
        chronological_age=body.get("chronological_age", 50),
    )
    return report
"""
