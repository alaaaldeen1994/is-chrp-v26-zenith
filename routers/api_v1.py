import os
import time
import uuid
import numpy as np
from fastapi import APIRouter, Depends, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import AuditLog
from schemas.requests import (
    LNPOptimizeRequest,
    PerturbationRequest,
    SafetyAuditRequest,
    DiscoveryRequest,
    VirtualTrialRequest,
    ProteinFoldingRequest
)
from schemas.responses import APIEnvelope, AsyncJobResponse
from config.settings import settings

# Lazy import services to prevent startup memory overhead
_lnp_optimizer = None
_multiomics_service = None
_structural_folder = None
_census_client = None

def get_lnp_optimizer():
    global _lnp_optimizer
    if _lnp_optimizer is None:
        from services.lnp_optimizer import LNPOptimizerService
        _lnp_optimizer = LNPOptimizerService()
    return _lnp_optimizer

def get_multiomics_service():
    global _multiomics_service
    if _multiomics_service is None:
        from services.multiomics_service import MultiOmicsPredictorService
        _multiomics_service = MultiOmicsPredictorService()
    return _multiomics_service

def get_structural_folder():
    global _structural_folder
    if _structural_folder is None:
        from services.structural_folder import StructuralFolderService
        _structural_folder = StructuralFolderService()
    return _structural_folder

def get_census_client():
    global _census_client
    if _census_client is None:
        from utils.census_client import CensusClient
        _census_client = CensusClient()
    return _census_client

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# In-memory job state cache for local execution fallback
jobs_db = {}

# Simple in-memory rate limiter for UI-based protein folding proxy
UI_FOLD_LIMITS = {}

def check_ui_rate_limit(ip: str) -> bool:
    import time
    now = time.time()
    if ip not in UI_FOLD_LIMITS:
        UI_FOLD_LIMITS[ip] = []
    # Clean old timestamps (older than 60 seconds)
    UI_FOLD_LIMITS[ip] = [t for t in UI_FOLD_LIMITS[ip] if now - t < 60]
    if len(UI_FOLD_LIMITS[ip]) >= 10:
        return False
    UI_FOLD_LIMITS[ip].append(now)
    return True

# --- Helper function to log audit entries ---
def log_api_call(db: Session, request: Request, status_code: int, duration_ms: int, credits_used: int):
    api_key_id = getattr(request.state, "api_key_id", None)
    if not api_key_id:
        api_key = getattr(request.state, "api_key", None)
        try:
            api_key_id = api_key.id if api_key else None
        except Exception:
            api_key_id = None
            
    log = AuditLog(
        api_key_id=api_key_id,
        endpoint=request.url.path,
        method=request.method,
        status_code=status_code,
        ip_address=request.client.host if request.client else None,
        compute_time_ms=duration_ms,
        credits_used=credits_used
    )
    db.add(log)
    db.commit()

# --- Health Check ---
@router.get("/health", response_model=APIEnvelope)
def get_health(request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    data = {
        "status": "online",
        "timestamp": int(start_time),
        "engine": "Zenith-Sim Core v30.0",
        "mode": settings.ENV
    }
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 0)
    return APIEnvelope(data=data, meta={"compute_time_ms": duration, "credits_used": 0})

@router.get("/reference/genes", response_model=APIEnvelope)
def get_genes(request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        from bridge_server import GENE_SYMBOLS
        genes = GENE_SYMBOLS
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback to general list if bridge is not importable
        genes = ["POU5F1", "SOX2", "NANOG", "LIN28A", "KLF4", "MYC", "GATA4", "TBX5", "NKX2-5", "SIRT1", "SIRT5", "SIRT6"]
    
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 0)
    return APIEnvelope(data={"total": len(genes), "genes": genes}, meta={"compute_time_ms": duration, "credits_used": 0})

# --- LNP Optimization ---
@router.post("/lnp/optimize", response_model=APIEnvelope)
def post_lnp_optimize(
    payload: LNPOptimizeRequest, 
    request: Request, 
    db: Session = Depends(get_db),
    optimizer = Depends(get_lnp_optimizer)
):
    start_time = time.time()
    
    # Verify molar ratio sum is 1.0 (with small float tolerance)
    ratios = payload.molar_ratios
    total_ratio = sum(ratios.values())
    if abs(total_ratio - 1.0) > 0.05:
        raise HTTPException(status_code=400, detail="Molar ratios must sum to 1.0 (100%)")

    # Adapt inputs to structure expected by evaluate_formulation
    molar_ratios = dict(ratios)
    if "active_targeting" not in molar_ratios:
        if payload.ligand_density > 0.0:
            molar_ratios["active_targeting"] = payload.ligand_density
        else:
            molar_ratios["active_targeting"] = 2.5 if payload.active_ligand_conjugation else 0.0
    molar_ratios["peg_mw"] = payload.peg_mw
    
    # Run PyTorch surrogate inference
    predictions = optimizer.evaluate_formulation(
        molar_ratios=molar_ratios,
        np_ratio=payload.np_ratio
    )
    
    data = {
        "circulation_half_life_hours": float(predictions["circulation_half_life_hours"]),
        "heart_selectivity_score": float(predictions["heart_selectivity_score"]),
        "liver_sequestration_score": float(predictions["liver_sequestration_score"]),
        "endosomal_escape_percent": float(predictions["endosomal_escape_percent"]),
        "particle_size_nm": float(predictions["biophysical_metrics"]["particle_size_nm"]),
        "zeta_potential_mv": float(predictions["biophysical_metrics"]["zeta_potential_mv"]),
        "encapsulation_efficiency_percent": float(predictions["encapsulation_efficiency_percent"]),
        "cytotoxicity_index": float(predictions["cytotoxicity_index"]),
        "formulation_status": predictions.get("formulation_status"),
        "delivery_mechanism": predictions.get("delivery_mechanism"),
        "mechanism_note": predictions.get("mechanism_note")
    }
    
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 1)
    return APIEnvelope(data=data, meta={"compute_time_ms": duration, "credits_used": 1})

# --- Multi-Omics Perturbation (Decommissioned) ---
@router.post("/predict/perturbation")
def post_predict_perturbation():
    raise HTTPException(
        status_code=410,
        detail="Endpoint decommissioned. Multi-omics perturbation prediction has been removed."
    )

# --- Safety & Clock Audit (Decommissioned) ---
@router.post("/safety/audit")
def post_safety_audit():
    raise HTTPException(
        status_code=410,
        detail="Endpoint decommissioned. Epigenetic clock and pioneer safety audit heuristics have been removed."
    )

# --- Async Job Check Status ---
@router.get("/jobs/{job_id}", response_model=APIEnvelope)
def get_job_status(job_id: str, request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 0)
    return APIEnvelope(data=job, meta={"compute_time_ms": duration, "credits_used": 0})

# --- Async Discovery Job Launcher ---
def run_local_discovery_task(job_id: str, payload: DiscoveryRequest):
    jobs_db[job_id]["status"] = "running"
    try:
        time.sleep(4) # Simulate calculation latency
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["result"] = {
            "recommended_protocol": ["GATA4", "TBX5", "SIRT1"],
            "confidence": 0.89,
            "scientific_rationale": f"Identified pioneer factors for: {payload.target_query}",
            "synergy_score": 94.2
        }
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

@router.post("/discover/run", response_model=AsyncJobResponse, status_code=202)
def post_discover_run(
    payload: DiscoveryRequest, 
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    job_id = str(uuid.uuid4())
    status_url = f"{request.base_url}api/v1/jobs/{job_id}"
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "status_url": status_url,
        "eta_seconds": 4.0
    }
    background_tasks.add_task(run_local_discovery_task, job_id, payload)
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 202, duration, 5)
    return AsyncJobResponse(job_id=job_id, status="pending", status_url=status_url, eta_seconds=4.0)

# --- Async Reprogramming Job Launcher ---
def run_local_reprogramming_task(job_id: str, prompt: str, cell_type: str):
    jobs_db[job_id]["status"] = "running"
    try:
        from partial_safety import filter_for_partial_reprogramming, score_sirtuin_pathway
        time.sleep(5) # Simulate pathway search
        
        candidates = ["GATA4", "TBX5", "MEF2C", "SIRT1"]
        audit_report = filter_for_partial_reprogramming(candidates, "balanced", 0.5)
        sirt_report = score_sirtuin_pathway(candidates)
        
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["result"] = {
            "prompt": prompt,
            "cell_type": cell_type,
            "approved_candidates": [item["gene"] for item in audit_report.get("approved", [])],
            "blocked_candidates": audit_report.get("blocked", []),
            "sirtuin_activity_score": sirt_report.get("pathway_score", 0),
            "af3_manifest": {
                "name": "Zenith_AF3_Job",
                "sequences": [
                    {"id": "GATA4", "sequence": "MAP..."},
                    {"id": "SIRT1", "sequence": "MAD..."}
                ]
            }
        }
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

@router.post("/reprogramming/run", response_model=AsyncJobResponse, status_code=202)
def post_reprogramming_run(
    prompt: str,
    cell_type: str = "ventricular_myocyte",
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    job_id = str(uuid.uuid4())
    status_url = f"{request.base_url}api/v1/jobs/{job_id}"
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "status_url": status_url,
        "eta_seconds": 5.0
    }
    background_tasks.add_task(run_local_reprogramming_task, job_id, prompt, cell_type)
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 202, duration, 5)
    return AsyncJobResponse(job_id=job_id, status="pending", status_url=status_url, eta_seconds=5.0)

# --- Virtual Trials Simulation (Decommissioned) ---
@router.post("/trials/run")
def post_trials_run():
    raise HTTPException(
        status_code=410,
        detail="Endpoint decommissioned. Virtual trial simulation has been removed."
    )

# --- ESMFold 3D Structure Folding (Decommissioned) ---
@router.post("/structure/fold")
@router.post("/structure/fold/ui")
def post_structure_fold():
    raise HTTPException(
        status_code=410,
        detail="Endpoint decommissioned. Structure prediction fallback has been removed."
    )

# --- AnnData File Download Endpoint ---
@router.get("/jobs/{job_id}/download")
def get_job_download(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    job = jobs_db.get(job_id)
    if not job or "filepath" not in job:
        raise HTTPException(status_code=404, detail="AnnData download file not found for this job")
        
    filepath = job["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="AnnData file has expired or was deleted from server cache")
        
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 0)
    
    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        media_type="application/octet-stream",
        filename=filename
    )


