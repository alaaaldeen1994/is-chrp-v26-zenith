"""
LNP Delivery Optimizer v2 Router — Zenith Phase 3
POST /api/v2/lnp/optimize-v2
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.lnp_optimizer_v2 import run_lnp_optimization_v2

router = APIRouter(prefix="/api/v2/lnp", tags=["LNP Delivery Optimization v2"])


class LNPOptimizeRequest(BaseModel):
    target_organ: str = Field(
        default="heart",
        description="Target organ for delivery: 'heart', 'liver', 'lung', 'spleen', 'brain'",
    )
    payload_type: str = Field(
        default="Prime Editor pegRNA",
        description="Payload type: 'mRNA', 'Prime Editor pegRNA', 'Cas9 RNP', 'DNA plasmid'",
    )
    payload_size_kb: float = Field(
        default=4.5,
        ge=0.1,
        le=50.0,
        description="Payload length in kilobases",
    )
    payload_sequence: Optional[str] = Field(
        default=None,
        description="Optional RNA/DNA sequence for PAMP immunogenicity scan",
    )
    desired_diameter_nm: float = Field(
        default=80.0,
        ge=30.0,
        le=300.0,
        description="Target LNP particle diameter in nm",
    )


class LNPOptimizeResponse(BaseModel):
    delivery_job: Dict[str, Any]
    sort_formulation: Dict[str, Any]
    delivery_performance: Dict[str, Any]
    immunogenicity_pamp_scan: Dict[str, Any]
    microfluidic_formulation_protocol: Dict[str, Any]
    summary: str


@router.post(
    "/optimize-v2",
    response_model=LNPOptimizeResponse,
    summary="Optimize LNP Formulation with SORT Organ Tropism",
    description="""
Designs 5-component lipid nanoparticles (LNPs) with Selective Organ Targeting (SORT technology).

**Supported Organs**: Heart, Liver, Lung, Spleen, Brain.

**Outputs**:
- 5-lipid formulation ratios (Ionizable, Helper, Cholesterol, PEG, SORT lipid)
- Ionizable lipid $pK_a$ endosomal escape assessment
- Organ tropism selectivity % and encapsulation efficiency %
- Optimal N/P ratio
- PAMP TLR7/8 immunogenicity scan
- Microfluidic mixing protocol
    """,
)
async def optimize_lnp_v2(request: LNPOptimizeRequest) -> LNPOptimizeResponse:
    try:
        result = run_lnp_optimization_v2(
            target_organ=request.target_organ,
            payload_type=request.payload_type,
            payload_size_kb=request.payload_size_kb,
            payload_sequence=request.payload_sequence,
            desired_diameter_nm=request.desired_diameter_nm,
        )
        return LNPOptimizeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LNP optimization v2 error: {str(e)}")


@router.get(
    "/optimize-v2/demo",
    summary="Demo: Cardiac LNP formulation for Prime Editor pegRNA",
)
async def lnp_v2_demo() -> Dict[str, Any]:
    result = run_lnp_optimization_v2(
        target_organ="heart",
        payload_type="Prime Editor pegRNA",
        payload_size_kb=4.5,
    )
    result["demo"] = True
    return result
