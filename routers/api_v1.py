import time
import uuid
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import AuditLog
from schemas.requests import (
    LNPOptimizeRequest,
    PerturbationRequest,
    SafetyAuditRequest,
    DiscoveryRequest,
    VirtualTrialRequest
)
from schemas.responses import APIEnvelope, AsyncJobResponse
from config.settings import settings

# Lazy import services to prevent startup memory overhead
_lnp_optimizer = None
_multiomics_service = None

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

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# In-memory job state cache for local execution fallback
jobs_db = {}

# --- Helper function to log audit entries ---
def log_api_call(db: Session, request: Request, status_code: int, duration_ms: int, credits_used: int):
    api_key = getattr(request.state, "api_key", None)
    log = AuditLog(
        api_key_id=api_key.id if api_key else None,
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

# --- Reference: Genes ---
@router.get("/reference/genes", response_model=APIEnvelope)
def get_genes(request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        from bridge_server import CONFIG
        genes = CONFIG.geneSymbols
    except Exception:
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

# --- Multi-Omics Perturbation ---
@router.post("/predict/perturbation", response_model=APIEnvelope)
def post_predict_perturbation(
    payload: PerturbationRequest, 
    request: Request, 
    db: Session = Depends(get_db),
    predictor = Depends(get_multiomics_service)
):
    start_time = time.time()
    
    result = predictor.predict_perturbation_trajectory(
        baseline_cell_type=payload.baseline_cell_type,
        factors=payload.perturbation_factors
    )
    
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 2)
    return APIEnvelope(data=result, meta={"compute_time_ms": duration, "credits_used": 2})

# --- Safety & Clock Audit ---
@router.post("/safety/audit", response_model=APIEnvelope)
def post_safety_audit(
    payload: SafetyAuditRequest, 
    request: Request, 
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    from partial_safety import (
        filter_for_partial_reprogramming,
        score_sirtuin_pathway,
        score_horvath_impact
    )
    
    # 1. Pioneer factor filter
    audit_report = filter_for_partial_reprogramming(
        candidates=payload.factors,
        mode="balanced",
        bio_age=0.5
    )
    
    # 2. Sirtuin engagement
    sirt_report = score_sirtuin_pathway(payload.factors)
    
    # 3. Horvath clock loci hit rate
    horvath_report = score_horvath_impact(payload.factors)
    
    data = {
        "approved_factors": [item["gene"] for item in audit_report.get("approved", [])],
        "blocked_factors": audit_report.get("blocked", []),
        "sirtuin_engagement": sirt_report,
        "horvath_clock_impact": horvath_report,
        "safety_summary": audit_report.get("safety_summary", "")
    }
    
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 1)
    return APIEnvelope(data=data, meta={"compute_time_ms": duration, "credits_used": 1})

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
            "age_reduction_estimate_years": 11.9,
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

# --- Async Virtual Trial Launcher ---
def run_local_trial_task(job_id: str, payload: VirtualTrialRequest):
    jobs_db[job_id]["status"] = "running"
    try:
        from bridge_server import get_dosage_optimizer
        time.sleep(6) # Simulate SDE cohort trajectories
        
        # Build dummy trial telemetry
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["result"] = {
            "disease": payload.disease,
            "protocol": payload.protocol,
            "cohort_size": payload.cohort_size,
            "p_value": 0.0034,
            "average_age_reduction_years": 9.4,
            "kaplan_meier_active_survival": [1.0, 0.98, 0.95, 0.92, 0.89],
            "kaplan_meier_placebo_survival": [1.0, 0.94, 0.88, 0.82, 0.74],
            "responder_status": "highly_significant"
        }
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)

@router.post("/trials/run", response_model=AsyncJobResponse, status_code=202)
def post_trials_run(
    payload: VirtualTrialRequest,
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
        "eta_seconds": 6.0
    }
    background_tasks.add_task(run_local_trial_task, job_id, payload)
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 202, duration, 10)
    return AsyncJobResponse(job_id=job_id, status="pending", status_url=status_url, eta_seconds=6.0)

