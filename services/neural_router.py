"""
Neural Analysis Router — implements /api/v1/neural/analyze

Called from profile.html to run the NEUROS-X cardiac neural age
simulation and arrhythmia safety check on a given ion-channel
expression profile.

Payload sent from profile.html:
    {
        "expression": { "SCN5A": 10.0, "KCNH2": 0.2, ... },
        "chronological_age": 50.0   (optional)
    }

Response consumed by profile.html:
    {
        "safety_classification": "SAFE" | "WARNING" | "ERROR",
        "ecg_proxy": [...],          -- float list for ECG plot
        "neural_age": 58.3,
        "phi_hat": 0.72,
        "synchrony": 0.85,
        "reason": "..."
    }
"""

from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class NeuralAnalyzeRequest(BaseModel):
    expression: Dict[str, float]
    chronological_age: Optional[float] = 50.0


@router.post("/api/v1/neural/analyze")
async def neural_analyze(req: NeuralAnalyzeRequest):
    """
    FIX 8: Neural cardiac analysis endpoint.
    Previously 42-byte empty router — now fully implemented.

    Runs two analyses in sequence:
      1. NeuralAgeClock — estimates cardiac neural biological age
         from the expression levels of known neural-ageing markers.
      2. NEUROS-X CardiacNeuralSubstrate — simulates the cardiac
         electrical network and checks for fibrillation risk.
    """
    try:
        # --- Step 1: Neural Age Clock ---
        from services.neural_age_clock import get_neural_clock

        clock = get_neural_clock()
        neural_age, confidence, breakdown = clock.predict(
            expression_vector=req.expression,
            chronological_age=req.chronological_age,
        )

        # --- Step 2: NEUROS-X Arrhythmia Substrate ---
        from services.neuros_substrate_service import get_substrate_service

        svc = get_substrate_service()
        fib_check = svc.substrate.check_fibrillation_risk(req.expression)
        safety_audit = svc.substrate.audit_arrhythmia_risk(req.expression)

        classification = safety_audit.get("safety_classification", "WARNING")
        ecg_proxy = safety_audit.get("ecg_proxy", [])
        phi_hat = safety_audit.get("phi_hat", 0.0)
        synchrony = safety_audit.get("synchrony", 0.0)
        reason = safety_audit.get("reason", "Analysis complete.")

        return {
            "safety_classification": classification,
            "ecg_proxy": ecg_proxy,
            "neural_age": round(float(neural_age), 1),
            "neural_age_confidence": round(float(confidence), 3),
            "phi_hat": round(float(phi_hat), 4),
            "synchrony": round(float(synchrony), 4),
            "reason": reason,
            "fibrillation_detected": fib_check.get("fibrillation_detected", False),
            "n_markers_detected": breakdown.get("n_markers_detected", 0),
            "chronological_age": req.chronological_age,
            "status": "ok"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "safety_classification": "ERROR",
            "ecg_proxy": [],
            "neural_age": None,
            "phi_hat": 0.0,
            "synchrony": 0.0,
            "reason": f"Neural analysis failed: {str(e)[:200]}",
            "status": "error"
        }
