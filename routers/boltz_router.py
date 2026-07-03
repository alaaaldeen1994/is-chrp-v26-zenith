"""
boltz_router.py - Zenith Boltz API Endpoints
==========================================
All endpoints under /api/v1/structure/boltz/

Security:
  - BOLTZ_API_KEY never returned to client
  - Stack traces stripped from error responses
  - CIF and confidence files proxied (no direct Boltz URLs exposed)
  - Rate limiting: BOLTZ_API_MAX_JOBS_PER_USER_PER_DAY enforced in-memory
"""

import time
from collections import defaultdict
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from config.settings import settings

# ── Rate limiter (per IP, in-memory) ─────────────────────────────────────────
_BOLTZ_DAILY_COUNTS: Dict[str, list] = defaultdict(list)

def _check_boltz_rate_limit(ip: str) -> bool:
    now = time.time()
    day_ago = now - 86400
    _BOLTZ_DAILY_COUNTS[ip] = [t for t in _BOLTZ_DAILY_COUNTS[ip] if t > day_ago]
    if len(_BOLTZ_DAILY_COUNTS[ip]) >= settings.BOLTZ_API_MAX_JOBS_PER_USER_PER_DAY:
        return False
    _BOLTZ_DAILY_COUNTS[ip].append(now)
    return True

# ── Router ────────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/v1/structure/boltz", tags=["Boltz Complex Prediction"])

# ── Request/Response schemas ──────────────────────────────────────────────────
class ComplexEntity(BaseModel):
    type: str = Field(..., description="protein | dna | rna | ligand_ccd | ligand_smiles")
    value: str = Field(..., description="Sequence, CCD code, or SMILES string")
    chain_ids: list[str] = Field(default_factory=lambda: ["A"])

class BindingSpec(BaseModel):
    type: str = Field(..., description="ligand_protein_binding | protein_protein_binding")
    binder_chain_id: Optional[str] = None
    binder_chain_ids: Optional[list[str]] = None

class ComplexManifest(BaseModel):
    entities: list[ComplexEntity]
    binding: Optional[BindingSpec] = None

class ValidateRequest(BaseModel):
    manifest: ComplexManifest

class EstimateRequest(BaseModel):
    manifest: ComplexManifest

class SubmitRequest(BaseModel):
    manifest: ComplexManifest
    job_name: Optional[str] = Field(None, max_length=64)
    num_samples: int = Field(1, ge=1, le=5)


def _get_client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _import_boltz():
    """Lazy import of boltz_service to avoid startup overhead."""
    import services.boltz_service as bs
    return bs


def _format_error(code: str, message: str) -> Dict[str, Any]:
    return {"status": "error", "error_code": code, "message": message}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/validate")
async def validate_manifest(body: ValidateRequest):
    """
    Validate a complex manifest before submission.
    Returns: { valid, errors, warnings, summary }
    """
    bs = _import_boltz()
    manifest_dict = {"entities": [e.dict() for e in body.manifest.entities]}
    result = bs.validate_complex_manifest(manifest_dict)
    return result


@router.post("/estimate")
async def estimate_cost(body: EstimateRequest, request: Request):
    """
    Get a USD cost estimate for a complex prediction job.
    Returns: { estimated_cost_usd, breakdown, disclaimer }
    """
    bs = _import_boltz()
    manifest_dict = {"entities": [e.dict() for e in body.manifest.entities]}

    try:
        result = bs.estimate_boltz_cost(manifest_dict)
        return result
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.post("/submit")
async def submit_job(body: SubmitRequest, request: Request):
    """
    Submit a real Boltz API complex prediction job.
    Returns: { boltz_prediction_id, status, model, real_prediction, synthetic_fallback }

    CRITICAL: COMPLEX_SYNTHETIC_FALLBACK=false enforced — no fake CIF ever generated.
    """
    bs = _import_boltz()

    # Kill switch
    if not settings.BOLTZ_API_ENABLED:
        raise HTTPException(
            status_code=503,
            detail=_format_error("boltz_disabled", "Boltz API is disabled. Contact administrator.")
        )

    # Rate limit
    ip = _get_client_ip(request)
    if not _check_boltz_rate_limit(ip):
        raise HTTPException(
            status_code=429,
            detail=_format_error(
                "rate_limit",
                f"Daily Boltz job limit ({settings.BOLTZ_API_MAX_JOBS_PER_USER_PER_DAY}) exceeded."
            )
        )

    manifest_dict = {"entities": [e.dict() for e in body.manifest.entities]}

    # Validate first
    validation = bs.validate_complex_manifest(manifest_dict)
    if not validation["valid"]:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "error_code": "validation_failed",
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }
        )

    # Build binding spec
    binding_dict = None
    if body.manifest.binding:
        binding_dict = body.manifest.binding.dict(exclude_none=True)

    try:
        prediction = bs.submit_boltz_job(
            manifest=manifest_dict,
            job_name=body.job_name,
            num_samples=body.num_samples,
            binding=binding_dict,
        )
        return {
            "boltz_prediction_id": prediction.get("id"),
            "status": prediction.get("status"),
            "model": prediction.get("model", "boltz-2.1"),
            "real_prediction": True,
            "synthetic_fallback": False,
        }
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}")
async def get_job_status(boltz_prediction_id: str):
    """
    Poll the status of a Boltz prediction job.
    Returns: { id, status, model, real_prediction, synthetic_fallback }
    """
    bs = _import_boltz()
    try:
        raw = bs.get_boltz_job_status(boltz_prediction_id)
        return {
            "id": raw.get("id"),
            "status": raw.get("status"),
            "model": raw.get("model"),
            "real_prediction": True,
            "synthetic_fallback": False,
            "error": raw.get("error"),
        }
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}/result")
async def get_job_result(boltz_prediction_id: str):
    """
    Get the full result metadata for a completed Boltz prediction.
    Returns: { id, status, model, num_samples, best_sample, all_sample_metrics,
               binding_metrics, real_prediction, synthetic_fallback }
    Note: Raw Boltz download URLs are NOT included. Use /download endpoints.
    """
    bs = _import_boltz()
    try:
        result = bs.get_boltz_job_result(boltz_prediction_id)
        # Strip internal fields before returning to client
        public_result = {k: v for k, v in result.items() if not k.startswith("_internal")}
        return public_result
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}/download/model.cif")
async def download_cif(
    boltz_prediction_id: str,
    sample: int = Query(0, ge=0, le=4),
):
    """
    Download the predicted CIF structure file for a given sample index.
    Proxied through Zenith backend — Boltz URLs are NOT exposed to the browser.
    """
    bs = _import_boltz()
    try:
        cif_bytes = bs.download_boltz_cif_content(boltz_prediction_id, sample_index=sample)
        return Response(
            content=cif_bytes,
            media_type="chemical/x-cif",
            headers={
                "Content-Disposition": f'attachment; filename="boltz_{boltz_prediction_id}_sample{sample}.cif"',
                "X-Real-Prediction": "true",
                "X-Synthetic-Fallback": "false",
            }
        )
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}/download/model.pdb")
async def download_pdb(
    boltz_prediction_id: str,
    sample: int = Query(0, ge=0, le=4),
):
    """
    Download the predicted structure converted to standard PDB format.
    Proxied through Zenith backend.
    """
    bs = _import_boltz()
    try:
        pdb_bytes = bs.download_boltz_pdb_content(boltz_prediction_id, sample_index=sample)
        return Response(
            content=pdb_bytes,
            media_type="chemical/x-pdb",
            headers={
                "Content-Disposition": f'attachment; filename="boltz_{boltz_prediction_id}_sample{sample}.pdb"',
                "X-Real-Prediction": "true",
                "X-Synthetic-Fallback": "false",
            }
        )
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}/download/confidence.json")
async def download_confidence(boltz_prediction_id: str):
    """
    Download the confidence/metrics JSON for all samples.
    Proxied through Zenith backend.
    """
    bs = _import_boltz()
    try:
        conf_bytes = bs.download_boltz_confidence_content(boltz_prediction_id)
        return Response(
            content=conf_bytes,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="boltz_{boltz_prediction_id}_confidence.json"',
                "X-Real-Prediction": "true",
                "X-Synthetic-Fallback": "false",
            }
        )
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.get("/jobs/{boltz_prediction_id}/pae")
async def get_job_pae(boltz_prediction_id: str):
    """
    Retrieve the 2D Predicted Aligned Error (PAE) matrix for a completed prediction.
    """
    bs = _import_boltz()
    try:
        return bs.get_boltz_job_pae(boltz_prediction_id)
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))


@router.delete("/jobs/{boltz_prediction_id}/data")
async def delete_job_data(boltz_prediction_id: str):
    """
    Eagerly delete all data for a completed Boltz prediction job.
    This is irreversible.
    """
    bs = _import_boltz()
    try:
        bs.delete_boltz_job_data(boltz_prediction_id)
        return {"status": "deleted", "prediction_id": boltz_prediction_id}
    except bs.BoltzDisabledError as exc:
        raise HTTPException(status_code=503, detail=_format_error("boltz_disabled", str(exc)))
    except bs.BoltzJobError as exc:
        raise HTTPException(status_code=502, detail=_format_error("boltz_api_error", str(exc)))
