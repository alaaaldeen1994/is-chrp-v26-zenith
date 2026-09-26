"""
MOFA+ Multi-Omics Router — Zenith Phase 2
POST /api/v2/multiomics/integrate (Decommissioned)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/api/v2/multiomics", tags=["Multi-Omics Integration (MOFA+)"])


class MultiOmicsRequest(BaseModel):
    sample_id: str = Field(
        default="PATIENT_001",
        description="Patient or cell sample identifier",
    )
    modalities_included: Optional[List[str]] = Field(
        default=None,
        description="List of modalities to integrate",
    )
    n_factors: int = Field(
        default=10,
        ge=2,
        le=20,
        description="Number of latent factors to extract",
    )


class MultiOmicsResponse(BaseModel):
    sample: Dict[str, Any]
    modality_total_variance_explained_percent: Dict[str, Any]
    latent_factor_loadings: List[Dict[str, Any]]
    dominant_patient_factors: List[Dict[str, Any]]
    transcriptomic_shift_score: Optional[float] = None
    multiomic_therapeutic_targets: List[Dict[str, Any]]
    summary: str


@router.post(
    "/integrate",
    summary="Integrate Multi-Omics Data (Decommissioned)",
    description="Multi-omics integration endpoint has been decommissioned.",
)
async def integrate_multiomics(request: MultiOmicsRequest):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="The /api/v2/multiomics/integrate endpoint has been decommissioned."
    )


@router.get(
    "/integrate/demo",
    summary="Demo: 5-Omics Integration (Decommissioned)",
)
async def multiomics_demo():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="The /api/v2/multiomics/integrate/demo endpoint has been decommissioned."
    )
