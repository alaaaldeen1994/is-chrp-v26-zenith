"""
boltz_service.py - Zenith Native Complex Prediction via Boltz API
Security rules:
  * BOLTZ_API_KEY is ONLY read from settings (Railway env var).
  * Key is NEVER included in any response, log line, or error dict.
  * COMPLEX_SYNTHETIC_FALLBACK must be False - raises BoltzJobError instead of fake coords.
  * All Boltz download URLs proxied through this service.
"""

import re
import json
import uuid
import httpx
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Endpoints ─────────────────────────────────────────────────────────────────
BOLTZ_ENDPOINT_START    = "/compute/v1/predictions/structure-and-binding"
BOLTZ_ENDPOINT_POLL     = "/compute/v1/predictions/structure-and-binding/{id}"
BOLTZ_ENDPOINT_ESTIMATE = "/compute/v1/predictions/structure-and-binding/estimate-cost"
BOLTZ_ENDPOINT_DELETE   = "/compute/v1/predictions/structure-and-binding/{id}/delete-data"
BOLTZ_TERMINAL_STATES   = {"succeeded", "failed", "stopped"}

PROTEIN_ALPHABET = set("ACDEFGHIKLMNPQRSTVWYX")
DNA_ALPHABET     = set("ACGTN")
RNA_ALPHABET     = set("ACGUN")

# ── Exceptions ────────────────────────────────────────────────────────────────
class BoltzValidationError(Exception): pass
class BoltzJobError(Exception): pass
class BoltzDisabledError(Exception): pass

# ── Helpers ───────────────────────────────────────────────────────────────────
def _sanitize_error(msg: str) -> str:
    cleaned = re.sub(r'x-api-key[:\s]+\S+', 'x-api-key:****', msg, flags=re.IGNORECASE)
    cleaned = re.sub(r'sk_bc_\S+', '****', cleaned)
    cleaned = re.sub(r'Bearer\s+\S+', 'Bearer ****', cleaned)
    return cleaned

def _boltz_headers() -> Dict[str, str]:
    return {
        "x-api-key": settings.BOLTZ_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def _check_enabled():
    if not settings.BOLTZ_API_ENABLED:
        raise BoltzDisabledError("Boltz API is currently disabled. Set BOLTZ_API_ENABLED=true.")
    if not settings.BOLTZ_API_KEY:
        raise BoltzDisabledError("BOLTZ_API_KEY is not configured. Set it in Railway environment variables.")

def _safe_boltz_error(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        msg = data.get("message") or data.get("detail") or data.get("error") or str(data)
    except Exception:
        msg = resp.text[:300]
    return _sanitize_error(msg)

def _sanitize_job_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\-_]", "-", name.strip())
    return cleaned[:64] if cleaned else f"zenith-job-{uuid.uuid4().hex[:8]}"

# ── Validation ────────────────────────────────────────────────────────────────
def validate_complex_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    summary = {"proteins": 0, "dna": 0, "rna": 0, "ligands": 0, "total_chains": 0}

    entities = manifest.get("entities")
    if not entities or not isinstance(entities, list):
        errors.append("'entities' array is required and must not be empty.")
        return {"valid": False, "errors": errors, "warnings": warnings, "summary": summary}

    protein_count = dna_count = rna_count = ligand_count = 0
    used_chain_ids: set = set()

    for i, entity in enumerate(entities):
        etype = entity.get("type", "").lower()
        value = entity.get("value", "")
        chain_ids = entity.get("chain_ids", [])

        for cid in chain_ids:
            if cid in used_chain_ids:
                errors.append(f"Entity {i}: chain_id '{cid}' is already used by another entity.")
            used_chain_ids.add(cid)

        if any(c in str(value) for c in ["<", ">", "script", "javascript:", "\x00"]):
            errors.append(f"Entity {i}: value contains invalid or potentially dangerous characters.")
            continue

        if etype == "protein":
            protein_count += 1
            cleaned = value.strip().upper()
            if not cleaned:
                errors.append(f"Entity {i} (protein): sequence cannot be empty.")
            else:
                invalid = set(cleaned) - PROTEIN_ALPHABET
                if invalid:
                    errors.append(f"Entity {i} (protein): invalid amino acid characters: {sorted(invalid)}")
                if len(cleaned) > 2000:
                    warnings.append(f"Entity {i} (protein): sequence length {len(cleaned)} is large and may be slow.")
                if len(cleaned) < 3:
                    errors.append(f"Entity {i} (protein): sequence too short (min 3 residues).")
            if protein_count > settings.BOLTZ_API_MAX_PROTEIN_CHAINS:
                errors.append(f"Too many protein chains (max {settings.BOLTZ_API_MAX_PROTEIN_CHAINS}).")

        elif etype == "dna":
            dna_count += 1
            cleaned = value.strip().upper()
            if not cleaned:
                errors.append(f"Entity {i} (dna): sequence cannot be empty.")
            else:
                invalid = set(cleaned) - DNA_ALPHABET
                if invalid:
                    errors.append(f"Entity {i} (dna): invalid DNA characters: {sorted(invalid)}")
                if len(cleaned) < 3:
                    errors.append(f"Entity {i} (dna): sequence too short (min 3 nt).")
            if dna_count > settings.BOLTZ_API_MAX_DNA_CHAINS:
                errors.append(f"Too many DNA chains (max {settings.BOLTZ_API_MAX_DNA_CHAINS}).")

        elif etype == "rna":
            rna_count += 1
            cleaned = value.strip().upper()
            if not cleaned:
                errors.append(f"Entity {i} (rna): sequence cannot be empty.")
            else:
                invalid = set(cleaned) - RNA_ALPHABET
                if invalid:
                    errors.append(f"Entity {i} (rna): invalid RNA characters: {sorted(invalid)}")
                if len(cleaned) < 3:
                    errors.append(f"Entity {i} (rna): sequence too short (min 3 nt).")
            if rna_count > settings.BOLTZ_API_MAX_RNA_CHAINS:
                errors.append(f"Too many RNA chains (max {settings.BOLTZ_API_MAX_RNA_CHAINS}).")

        elif etype in ("ligand_ccd", "ligand_smiles"):
            ligand_count += 1
            if not value.strip():
                errors.append(f"Entity {i} ({etype}): value cannot be empty.")
            if ligand_count > settings.BOLTZ_API_MAX_LIGANDS:
                errors.append(f"Too many ligands/ions (max {settings.BOLTZ_API_MAX_LIGANDS}).")

        else:
            errors.append(f"Entity {i}: unknown type '{etype}'. Allowed: protein, dna, rna, ligand_ccd, ligand_smiles.")

    if protein_count == 0:
        errors.append("At least one protein entity is required for complex prediction.")

    summary = {
        "proteins": protein_count,
        "dna": dna_count,
        "rna": rna_count,
        "ligands": ligand_count,
        "total_chains": protein_count + dna_count + rna_count + ligand_count,
    }
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings, "summary": summary}

# ── Cost Estimation ────────────────────────────────────────────────────────────
def estimate_boltz_cost(manifest: Dict[str, Any]) -> Dict[str, Any]:
    _check_enabled()
    url = settings.BOLTZ_API_BASE_URL.rstrip("/") + BOLTZ_ENDPOINT_ESTIMATE
    body = {"model": "boltz-2.1", "input": manifest}
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=_boltz_headers(), json=body)
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error reaching Boltz API: {_sanitize_error(str(exc))}")
    if resp.status_code != 200:
        raise BoltzJobError(f"Boltz cost estimate failed (HTTP {resp.status_code}): {_safe_boltz_error(resp)}")
    return resp.json()

# ── Job Submission ─────────────────────────────────────────────────────────────
def submit_boltz_job(
    manifest: Dict[str, Any],
    job_name: Optional[str] = None,
    num_samples: int = 1,
    binding: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    _check_enabled()
    input_body: Dict[str, Any] = {
        "entities": manifest["entities"],
        "num_samples": num_samples,
    }
    if binding:
        input_body["binding"] = binding

    body: Dict[str, Any] = {"model": "boltz-2.1", "input": input_body}

    url = settings.BOLTZ_API_BASE_URL.rstrip("/") + BOLTZ_ENDPOINT_START
    logger.info("[Boltz] Submitting complex prediction: %s", job_name or "unnamed")

    try:
        with httpx.Client(timeout=float(settings.BOLTZ_API_TIMEOUT_SECONDS)) as client:
            resp = client.post(url, headers=_boltz_headers(), json=body)
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error submitting Boltz job: {_sanitize_error(str(exc))}")

    if resp.status_code not in (200, 201, 202):
        raise BoltzJobError(f"Boltz job submission failed (HTTP {resp.status_code}): {_safe_boltz_error(resp)}")

    prediction = resp.json()
    logger.info("[Boltz] Job submitted. ID: %s", prediction.get("id"))
    return prediction

# ── Status Polling ─────────────────────────────────────────────────────────────
def get_boltz_job_status(boltz_prediction_id: str) -> Dict[str, Any]:
    _check_enabled()
    url = settings.BOLTZ_API_BASE_URL.rstrip("/") + BOLTZ_ENDPOINT_POLL.format(id=boltz_prediction_id)
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=_boltz_headers())
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error polling Boltz job: {_sanitize_error(str(exc))}")
    if resp.status_code == 404:
        raise BoltzJobError(f"Boltz prediction '{boltz_prediction_id}' not found.")
    if resp.status_code != 200:
        raise BoltzJobError(f"Boltz status poll failed (HTTP {resp.status_code}): {_safe_boltz_error(resp)}")
    return resp.json()

# ── Result Retrieval ──────────────────────────────────────────────────────────
def get_boltz_job_result(boltz_prediction_id: str) -> Dict[str, Any]:
    prediction = get_boltz_job_status(boltz_prediction_id)
    status = prediction.get("status")
    if status == "failed":
        error_detail = prediction.get("error", {})
        raise BoltzJobError(f"Boltz prediction failed: {error_detail.get('message', 'unknown error')}")
    if status != "succeeded":
        raise BoltzJobError(f"Boltz prediction not yet complete (status: {status}).")

    output = prediction.get("output")
    if not output:
        raise BoltzJobError("Boltz prediction succeeded but returned no output data.")

    return {
        "id": prediction.get("id"),
        "status": "succeeded",
        "model": prediction.get("model"),
        "real_prediction": True,
        "synthetic_fallback": False,
        "num_samples": len(output.get("all_sample_results", [])),
        "best_sample": {"metrics": (output.get("best_sample") or {}).get("metrics", {})},
        "all_sample_metrics": [s.get("metrics", {}) for s in output.get("all_sample_results", [])],
        "binding_metrics": output.get("binding_metrics"),
        # Internal fields for proxied download - not exposed directly to browser
        "_internal_sample_urls": [
            {
                "url": s.get("structure", {}).get("url"),
                "url_expires_at": s.get("structure", {}).get("url_expires_at"),
            }
            for s in output.get("all_sample_results", [])
        ],
        "_internal_archive_url": output.get("archive", {}).get("url"),
        "_internal_archive_expires_at": output.get("archive", {}).get("url_expires_at"),
    }

# ── Proxied CIF Download ───────────────────────────────────────────────────────
def download_boltz_cif_content(boltz_prediction_id: str, sample_index: int = 0) -> bytes:
    result = get_boltz_job_result(boltz_prediction_id)
    internal_urls = result.get("_internal_sample_urls", [])

    if sample_index >= len(internal_urls):
        raise BoltzJobError(f"Sample index {sample_index} out of range (prediction has {len(internal_urls)} samples).")

    url_info = internal_urls[sample_index]
    cif_url = url_info.get("url")
    expires_at = url_info.get("url_expires_at")

    if not cif_url:
        raise BoltzJobError("CIF download URL is not available.")

    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                raise BoltzJobError("CIF download URL has expired. Re-fetch the result to get a fresh URL.")
        except (ValueError, AttributeError):
            pass

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(cif_url)
        if resp.status_code != 200:
            raise BoltzJobError(f"CIF download failed (HTTP {resp.status_code}).")
        return resp.content
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error downloading CIF: {_sanitize_error(str(exc))}")

def download_boltz_confidence_content(boltz_prediction_id: str) -> bytes:
    result = get_boltz_job_result(boltz_prediction_id)
    confidence_data = {
        "prediction_id": boltz_prediction_id,
        "model": result.get("model"),
        "real_prediction": True,
        "synthetic_fallback": False,
        "best_sample_metrics": result.get("best_sample", {}).get("metrics", {}),
        "all_sample_metrics": result.get("all_sample_metrics", []),
        "binding_metrics": result.get("binding_metrics"),
    }
    return json.dumps(confidence_data, indent=2).encode("utf-8")

def get_boltz_job_pae(boltz_prediction_id: str) -> Dict[str, Any]:
    import io
    import tarfile
    import numpy as np

    result = get_boltz_job_result(boltz_prediction_id)
    archive_url = result.get("_internal_archive_url")
    if not archive_url:
        raise BoltzJobError("Archive URL is not available.")

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.get(archive_url)
        if resp.status_code != 200:
            raise BoltzJobError(f"Archive download failed (HTTP {resp.status_code}).")
        archive_bytes = resp.content
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error downloading archive: {_sanitize_error(str(exc))}")

    try:
        pae_data = None
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("pae.npz"):
                    f = tar.extractfile(member)
                    if f:
                        pae_data = f.read()
                        break
        if not pae_data:
            raise BoltzJobError("sample_0_pae.npz not found in output archive.")
    except Exception as e:
        raise BoltzJobError(f"Failed to extract PAE data from archive: {str(e)}")

    try:
        with np.load(io.BytesIO(pae_data)) as loader:
            # Boltz stores PAE under key 'pae'
            pae_matrix = loader["pae"]
    except Exception as e:
        raise BoltzJobError(f"Failed to load PAE numpy array: {str(e)}")

    n = pae_matrix.shape[0]
    max_res = 600
    if n > max_res:
        step = int(np.ceil(n / max_res))
        pae_matrix = pae_matrix[::step, ::step]
        n = pae_matrix.shape[0]

    # Convert float32 values to standard native python floats for JSON serialization
    pae_list = [[float(val) for val in row] for row in pae_matrix]

    return {
        "prediction_id": boltz_prediction_id,
        "pae": pae_list,
        "n": n
    }

# ── Data Deletion ─────────────────────────────────────────────────────────────
def delete_boltz_job_data(boltz_prediction_id: str) -> bool:
    _check_enabled()
    url = settings.BOLTZ_API_BASE_URL.rstrip("/") + BOLTZ_ENDPOINT_DELETE.format(id=boltz_prediction_id)
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=_boltz_headers())
    except httpx.RequestError as exc:
        raise BoltzJobError(f"Network error deleting Boltz job data: {_sanitize_error(str(exc))}")
    if resp.status_code not in (200, 204):
        raise BoltzJobError(f"Boltz data deletion failed (HTTP {resp.status_code}): {_safe_boltz_error(resp)}")
    logger.info("[Boltz] Data deleted for prediction: %s", boltz_prediction_id)
    return True
