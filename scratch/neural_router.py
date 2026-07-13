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

    Returns:
      - neural_age: predicted age (years)
      - neural_age_gap: neural_age - chronological_age (negative = younger)
      - confidence: 0..1
      - breakdown: per-gene contributions
      - phi_hat: substrate integration (if available)
      - interpretation: operational summary
    """
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        clock = get_neural_clock(substrate_service=svc)
        result = await clock.predict_with_substrate(
            req.expression, req.chronological_age
        )
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"neural age prediction failed: {_strip(e)}")
        raise HTTPException(500, f"Prediction failed: {_strip(e)}")


@router.post("/analyze")
async def analyze_substrate(req: AnalyzeRequest, request: Request):
    """Run the spiking substrate on an ion-channel expression profile.

    Returns phi_hat, synchrony, active_fraction, ecg_proxy, etc.
    """
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        result = await svc.analyze_ion_profile(req.expression, steps=req.steps)
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"substrate analysis failed: {_strip(e)}")
        raise HTTPException(500, f"Analysis failed: {_strip(e)}")


@router.post("/compare")
async def compare_profiles(req: CompareRequest, request: Request):
    """Compare substrate response before/after a perturbation.

    Shows how a gene perturbation changes the simulated cardiac electrical
    activity (phi_delta, synchrony_delta, stability assessment).
    """
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        result = await svc.compare_profiles(req.baseline, req.perturbed)
        result["timestamp"] = datetime.utcnow().isoformat()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"compare failed: {_strip(e)}")
        raise HTTPException(500, f"Comparison failed: {_strip(e)}")


@router.post("/dual-age")
async def dual_age_assessment(req: DualAgeRequest, request: Request):
    """Combined Horvath (epigenetic) + Neural (functional) age assessment.

    THE MARKETING METRIC — no competitor offers dual-age.

    Returns:
      - horvath_age: epigenetic age (from your horvath_clock.py)
      - neural_age: functional neural age (from this module)
      - dual_gap: neural - horvath (positive = neural aging faster)
      - phenotype: concordant | neural_dominant | genomic_dominant
      - phenotype_description: operational interpretation
      - rejuvenation_potential: high | moderate | low
      - summary: one-line headline
    """
    _check_rate_limit(request)
    try:
        svc = get_substrate_service()
        clock = get_neural_clock(substrate_service=svc)
        neural_result = await clock.predict_with_substrate(
            req.expression, req.chronological_age
        )
        dual = DualAgeComparator.compare(req.horvath_age, neural_result)
        dual["neural_breakdown"] = neural_result.get("breakdown")
        dual["timestamp"] = datetime.utcnow().isoformat()
        dual["endpoint"] = "neural_dual_age_v1"
        return dual
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"dual-age failed: {_strip(e)}")
        raise HTTPException(500, f"Dual-age assessment failed: {_strip(e)}")


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
