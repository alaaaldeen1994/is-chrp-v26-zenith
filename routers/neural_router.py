"""Neural Analysis Router — FastAPI endpoints for NEUROS-X integration.

Follows the same pattern as routers/boltz_router.py:
  - async handlers
  - Pydantic request/response models
  - strip stack traces on error
  - rate limiting (in-memory, IP-based — same as bridge_server.py)
  - SQLAlchemy caching via SHA-256

Endpoints:
  GET  /api/v1/neural/panel         — list neural age marker genes
  GET  /api/v1/neural/substrate     — substrate info (clusters, genes)
  POST /api/v1/neural/age           — predict neural age from expression
  POST /api/v1/neural/analyze       — substrate analysis (phi, ecg proxy)
  POST /api/v1/neural/compare       — before/after perturbation comparison
  POST /api/v1/neural/dual-age      — Horvath + Neural combined (THE METRIC)

Wire into bridge_server.py:
    from routers.neural_router import router as neural_router
    app.include_router(neural_router)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.neuros_substrate_service import get_substrate_service
from services.neural_age_clock import get_neural_clock, DualAgeComparator

logger = logging.getLogger("neural_router")
router = APIRouter(prefix="/api/v1/neural", tags=["neural"])


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, IP-based — same as bridge_server.py)
# ---------------------------------------------------------------------------

_RATE_LIMIT = 100  # requests per day per IP
_rate_log: Dict[str, List[float]] = defaultdict(list)


def _check_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    # purge entries older than 24h
    _rate_log[client_ip] = [t for t in _rate_log[client_ip] if now - t < 86400]
    if len(_rate_log[client_ip]) >= _RATE_LIMIT:
        raise HTTPException(429, "Daily neural analysis limit reached. Try again tomorrow.")
    _rate_log[client_ip].append(now)


def _strip(e: Exception) -> str:
    """Clean error message — never expose internals."""
    return f"{type(e).__name__}: {str(e)[:200]}"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ExpressionRequest(BaseModel):
    """Gene expression vector (typically from scVI decoder output)."""
    expression: Dict[str, float] = Field(
        ..., description="Gene symbol -> expression level (e.g. {\"CHAT\": 3.2, \"TH\": 2.1})"
    )
    chronological_age: float = Field(50.0, ge=0, le=120, description="Donor chronological age")
    use_cache: bool = Field(True, description="Use SHA-256 cached result if available")


class AnalyzeRequest(BaseModel):
    """Substrate analysis request (ion-channel profile -> phi/synchrony/ecg)."""
    expression: Dict[str, float] = Field(..., description="Ion-channel gene expression")
    steps: int = Field(50, ge=10, le=500, description="Simulation steps")


class CompareRequest(BaseModel):
    """Before/after perturbation comparison."""
    baseline: Dict[str, float] = Field(..., description="Pre-perturbation expression")
    perturbed: Dict[str, float] = Field(..., description="Post-perturbation expression")


class DualAgeRequest(BaseModel):
    """Combined Horvath + Neural age assessment (THE marketing metric)."""
    expression: Dict[str, float] = Field(..., description="Gene expression from scVI decoder")
    horvath_age: float = Field(..., ge=0, le=120, description="Horvath epigenetic age (from horvath_clock.py)")
    chronological_age: float = Field(50.0, ge=0, le=120, description="Donor chronological age")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/panel")
async def get_neural_panel():
    """List the neural age marker genes and their categories.

    Useful for documentation and for users to know which genes drive the
    neural age estimate.
    """
    clock = get_neural_clock()
    panel = clock.get_panel()
    return {
        "panel": panel,
        "n_markers": len(panel),
        "categories": list(set(v["category"] for v in panel.values())),
        "note": "Neural age markers for the intrinsic cardiac nervous system.",
    }


@router.get("/substrate")
async def get_substrate_info():
    """Return substrate configuration (clusters, genes, neuron count)."""
    svc = get_substrate_service()
    return {
        "n_neurons": svc.substrate.n_total,
        "n_edges": svc.substrate.n_edges,
        "n_clusters": svc.substrate.n_clusters,
        "cluster_names": await svc.get_cluster_names(),
        "ion_channel_genes": await svc.get_ion_genes(),
        "neural_marker_genes": await svc.get_neural_markers(),
        "model": "CardiacNeuralSubstrate v1.0",
        "neuron_model": "LIF (Leaky Integrate-and-Fire) with adaptive threshold",
        "topology": "Watts-Strogatz small-world (16 clusters, 4 hubs)",
        "disclaimer": "Research simulation. Not a clinical ECG simulator.",
    }


@router.post("/age")
async def predict_neural_age(req: ExpressionRequest, request: Request):
    """Predict the biological age of the cardiac nervous system.

    Returns Calibration mode response until Pearson r > 0.75 is achieved.
    """
    _check_rate_limit(request)
    return {
        "status": "Calibrating",
        "message": "NEUROS-X Neural Age Clock is currently in calibration. Re-training is underway with CZ CellxGene adult human heart neurons to optimize validation metrics (target Pearson r > 0.75, MAE < 8 years). Predictions are temporarily disabled to prevent mean-collapse output.",
        "neural_age": None,
        "chronological_age": req.chronological_age,
        "neural_age_gap": None,
        "confidence": 0.0,
        "phi_hat": None,
        "synchrony": None,
        "breakdown": {},
        "interpretation": "Calibration Mode: Model is undergoing tuning for target validation metrics.",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/analyze")
async def analyze_cocktail_safety(req: AnalyzeRequest, request: Request):
    """
    Audit a reprogramming cocktail for arrhythmia risk.
    
    Returns a safety classification: SAFE, WARNING, or BLOCKED.
    Uses the 512-neuron spiking cardiac substrate to simulate
    action potential propagation.
    """
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        result = svc.substrate.audit_arrhythmia_risk(req.expression)
        result["timestamp"] = datetime.utcnow().isoformat()
        result["endpoint"] = "neural_arrhythmia_audit_v1"
        return result
    except Exception as e:
        logger.error(f"arrhythmia audit failed: {_strip(e)}")
        raise HTTPException(500, f"Audit failed: {_strip(e)}")


@router.post("/compare")
async def compare_safety(req: CompareRequest, request: Request):
    """Compare arrhythmia risk before and after a perturbation."""
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        baseline = svc.substrate.audit_arrhythmia_risk(req.baseline)
        perturbed = svc.substrate.audit_arrhythmia_risk(req.perturbed)
        
        # Determine if the perturbation improved or worsened safety
        class_order = {"SAFE": 0, "WARNING": 1, "BLOCKED": 2}
        delta = class_order[perturbed["safety_classification"]] - class_order[baseline["safety_classification"]]
        
        if delta < 0:
            assessment = "IMPROVED: Perturbation reduced arrhythmia risk."
        elif delta > 0:
            assessment = "DEGRADED: Perturbation increased arrhythmia risk."
        else:
            assessment = "NEUTRAL: Safety classification unchanged."
        
        return {
            "ok": True,
            "baseline": baseline,
            "perturbed": perturbed,
            "assessment": assessment,
            "phi_delta": perturbed["phi_hat"] - baseline["phi_hat"],
            "synchrony_delta": perturbed["synchrony"] - baseline["synchrony"],
        }
    except Exception as e:
        logger.error(f"arrhythmia comparison failed: {_strip(e)}")
        raise HTTPException(500, f"Comparison failed: {_strip(e)}")


@router.post("/dual-age")
async def dual_age_assessment(req: DualAgeRequest, request: Request):
    """Combined Horvath (epigenetic) + Neural (functional) age assessment.

    Returns Calibration response until Pearson r > 0.75 is achieved.
    """
    _check_rate_limit(request)
    return {
        "status": "Calibrating",
        "message": "NEUROS-X Neural Age Clock is currently in calibration. Combined Dual-Age comparisons are temporarily disabled until the neural model achieves target validation metrics (Pearson r > 0.75, MAE < 8 years).",
        "horvath_age": req.horvath_age,
        "neural_age": None,
        "dual_gap": None,
        "phenotype": "calibrating",
        "phenotype_description": "Neural clock is currently undergoing calibration to improve Pearson r correlation and MAE.",
        "rejuvenation_potential": "calibrating",
        "summary": "Dual-Age Assessment: Calibrating Neural Model",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "neural_dual_age_v1"
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@router.get("/health")
async def neural_health():
    """Liveness check for the neural analysis service."""
    try:
        svc = get_substrate_service()
        return {
            "status": "ok",
            "substrate_loaded": svc._substrate is not None,
            "n_neurons": svc.substrate.n_total if svc._substrate else 0,
            "model": "NeuralAgeClock v1.0 + CardiacNeuralSubstrate v1.0",
        }
    except Exception as e:
        return {"status": "degraded", "error": _strip(e)}
