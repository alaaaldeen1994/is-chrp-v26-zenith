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
_horvath_clock = None
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

def get_horvath_clock():
    global _horvath_clock
    if _horvath_clock is None:
        from services.horvath_clock import HorvathClockService
        _horvath_clock = HorvathClockService()
    return _horvath_clock

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

@router.get("/reference/genes", response_model=APIEnvelope)
def get_genes(request: Request, db: Session = Depends(get_db)):
    start_time = time.time()
    error_msg = None
    try:
        from bridge_server import GENE_SYMBOLS
        genes = GENE_SYMBOLS
    except Exception as e:
        import traceback
        error_msg = f"{e}\n{traceback.format_exc()}"
        # Fallback to general list if bridge is not importable
        genes = ["POU5F1", "SOX2", "NANOG", "LIN28A", "KLF4", "MYC", "GATA4", "TBX5", "NKX2-5", "SIRT1", "SIRT5", "SIRT6"]
    
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 0)
    return APIEnvelope(data={"total": len(genes), "genes": genes}, meta={"compute_time_ms": duration, "credits_used": 0, "error": error_msg})

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
# --- Async Census Perturbation Task Runner ---
def run_local_census_perturbation_task(
    job_id: str, 
    payload: PerturbationRequest, 
    census_client, 
    predictor,
    api_key_id: int = None
):
    jobs_db[job_id]["status"] = "running"
    try:
        # 1. Fetch cell vectors from Census (falls back to synthetic cardiac cells if offline)
        census_data = census_client.fetch_donor_cells(
            organism="homo_sapiens",
            value_filter=payload.census_filter or "tissue_general == 'heart'",
            max_cells=50
        )
        
        expression_matrix = census_data["expression_matrix"]
        metadata_list = census_data["metadata"]
        genes = census_data["genes"]
        
        # 2. Simulate perturbation across the cell matrix
        # For each cell, we calculate regulatory shifts based on MultiOmicsPredictorService
        perturbed_matrix = expression_matrix.copy()
        
        for gene_name, dosage in payload.perturbation_factors.items():
            if gene_name in genes:
                col_idx = genes.index(gene_name)
                # Over-express the factor
                perturbed_matrix[:, col_idx] += float(dosage)
                
            # Cascade transcriptional activation matching Jasper PWM targets in predictor
            if gene_name in predictor.factor_regulatory_weights:
                weights = predictor.factor_regulatory_weights[gene_name]
                for target_gene, weight in weights.items():
                    if target_gene in genes:
                        target_idx = genes.index(target_gene)
                        perturbed_matrix[:, target_idx] += float(dosage) * weight
                        
        # Bound matrix values
        perturbed_matrix = np.clip(perturbed_matrix, 0.0, 50.0)
        
        # 3. Simulate latent UMAP coordinates (dim 2)
        num_cells = perturbed_matrix.shape[0]
        latent_coords = np.random.normal(0, 1.0, size=(num_cells, 2))
        # Project cardiac structural markers on UMAP space for visualization separation
        if "TNNT2" in genes:
            tnnt2_idx = genes.index("TNNT2")
            latent_coords[:, 0] += perturbed_matrix[:, tnnt2_idx] * 2.0
            
        # 4. Update metadata with predicted clock outcomes
        for i in range(num_cells):
            cell_factors = {k: float(v) for k, v in payload.perturbation_factors.items()}
            # Calculate single-cell metrics
            single_cell_report = predictor.predict_perturbation_trajectory(
                baseline_cell_type=payload.baseline_cell_type,
                factors=cell_factors
            )
            metadata_list[i]["predicted_age_delta"] = single_cell_report.get("predicted_age_delta", 0.0)
            metadata_list[i]["endothelial_rejuvenation_score"] = single_cell_report.get("endothelial_rejuvenation_score", 0.0)
            metadata_list[i]["sirtuin_activity_index"] = single_cell_report.get("sirtuin_activity_index", 0.0)
            
        # 5. Serialize matrix to AnnData (.h5ad) file
        from utils.anndata_helper import serialize_to_h5ad
        filepath = serialize_to_h5ad(
            genes=genes,
            expression_matrix=perturbed_matrix,
            latent_coords=latent_coords,
            obs_metadata=metadata_list
        )
        
        result_payload = {
            "cell_count": num_cells,
            "genes_count": len(genes),
            "source_dataset": census_data["source"],
            "download_url": f"/api/v1/jobs/{job_id}/download"
        }
        
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["filepath"] = filepath
        jobs_db[job_id]["result"] = result_payload
        print(f"[CensusPerturbation] Completed! AnnData serialized to: {filepath}")
        
        # Dispatch webhook completion notification
        if api_key_id:
            from routers.webhooks import dispatch_webhook_sync
            dispatch_webhook_sync(
                api_key_id=api_key_id,
                event_type="job.completed",
                data={
                    "job_id": job_id,
                    "status": "completed",
                    "result": result_payload
                }
            )
        
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        
        # Dispatch webhook failure notification
        if api_key_id:
            try:
                from routers.webhooks import dispatch_webhook_sync
                dispatch_webhook_sync(
                    api_key_id=api_key_id,
                    event_type="job.failed",
                    data={
                        "job_id": job_id,
                        "status": "failed",
                        "error": str(e)
                    }
                )
            except Exception:
                pass

# --- Multi-Omics Perturbation ---
@router.post("/predict/perturbation")
def post_predict_perturbation(
    payload: PerturbationRequest, 
    request: Request, 
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    predictor = Depends(get_multiomics_service),
    census_client = Depends(get_census_client)
):
    start_time = time.time()
    
    # If census_filter is provided, run asynchronously and serialize to .h5ad
    if payload.census_filter:
        job_id = str(uuid.uuid4())
        status_url = f"{request.base_url}api/v1/jobs/{job_id}"
        
        api_key = getattr(request.state, "api_key", None)
        api_key_id = api_key.id if api_key else None
        
        jobs_db[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "status_url": status_url,
            "eta_seconds": 6.0
        }
        
        background_tasks.add_task(
            run_local_census_perturbation_task,
            job_id,
            payload,
            census_client,
            predictor,
            api_key_id
        )
        
        duration = int((time.time() - start_time) * 1000)
        log_api_call(db, request, 202, duration, 5)
        response.status_code = 202
        return AsyncJobResponse(
            job_id=job_id,
            status="pending",
            status_url=status_url,
            eta_seconds=6.0
        )
        
    # Otherwise, run the default synchronous projection
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
    db: Session = Depends(get_db),
    horvath_clock = Depends(get_horvath_clock)
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
    
    # 3. Horvath clock calculation
    if payload.cpg_methylation:
        # Run actual 353-CpG Horvath mathematical predictor
        horvath_report = horvath_clock.calculate_age(payload.cpg_methylation)
    else:
        # Fallback to heuristic loci hit rate
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

# --- ESMFold 3D Structure Folding ---
@router.post("/structure/fold", response_model=APIEnvelope)
def post_structure_fold(
    payload: ProteinFoldingRequest,
    request: Request,
    db: Session = Depends(get_db),
    folder = Depends(get_structural_folder)
):
    start_time = time.time()
    
    result = folder.fold_sequence(payload.sequence)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    duration = int((time.time() - start_time) * 1000)
    log_api_call(db, request, 200, duration, 10)
    return APIEnvelope(data=result, meta={"compute_time_ms": duration, "credits_used": 10})

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


