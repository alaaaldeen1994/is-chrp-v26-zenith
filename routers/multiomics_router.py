"""
MOFA+ Multi-Omics Router — Zenith Phase 2
POST /api/v2/multiomics/integrate
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.multiomics_integration_engine import run_mofa_integration

router = APIRouter(prefix="/api/v2/multiomics", tags=["Multi-Omics Integration (MOFA+)"])


class MultiOmicsRequest(BaseModel):
    sample_id: str = Field(
        default="PATIENT_001",
        description="Patient or cell sample identifier",
    )
    modalities_included: Optional[List[str]] = Field(
        default=None,
        description="List of modalities to integrate: 'scRNA-seq', 'ATAC-seq', 'DNA_Methylation', 'Proteomics', 'Metabolomics'",
    )
    n_factors: int = Field(
        default=10,
        ge=2,
        le=20,
        description="Number of MOFA+ latent factors to extract",
    )


class MultiOmicsResponse(BaseModel):
    sample: Dict[str, Any]
    modality_total_variance_explained_percent: Dict[str, Any]
    latent_factor_loadings: List[Dict[str, Any]]
    dominant_patient_factors: List[Dict[str, Any]]
    horvath_epigenetic_age_delta_years: float
    multiomic_therapeutic_targets: List[Dict[str, Any]]
    summary: str


@router.post(
    "/integrate",
    response_model=MultiOmicsResponse,
    summary="Integrate Multi-Omics Data (MOFA+ Factor Analysis)",
    description="""
Learns low-dimensional latent factor representations across 5 omics modalities:
1. **scRNA-seq**: Transcriptome gene expression
2. **ATAC-seq**: Chromatin peak accessibility
3. **DNA Methylation**: Horvath Clock CpG beta values
4. **Proteomics**: Protein abundance
5. **Metabolomics**: Metabolite concentrations

**Outputs**:
- $K=10$ latent factors with per-modality variance explained ($R^2$)
- Patient-specific latent factor loadings vector
- Horvath epigenetic clock age delta prediction
- Ranked multi-omic therapeutic targets with action recommendations
    """,
)
async def integrate_multiomics(request: MultiOmicsRequest) -> MultiOmicsResponse:
    try:
        result = run_mofa_integration(
            sample_id=request.sample_id,
            modalities_included=request.modalities_included,
            n_factors=request.n_factors,
        )
        return MultiOmicsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-omics integration error: {str(e)}")


@router.get(
    "/integrate/demo",
    summary="Demo: 5-Omics Integration for Cardiac Patient 001",
)
async def multiomics_demo() -> Dict[str, Any]:
    result = run_mofa_integration(sample_id="PATIENT_CARDIA_001", n_factors=10)
    result["demo"] = True
    return result
