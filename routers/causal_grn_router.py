"""
Epistatic GRN Causal Router — Zenith Phase 2
POST /api/v2/grn/causal-map
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.epistatic_grn_mapper import run_causal_grn_map

router = APIRouter(prefix="/api/v2/grn", tags=["Epistatic GRN Causal Mapper"])


class GRNCausalRequest(BaseModel):
    target_gene: Optional[str] = Field(
        default="GATA4",
        description="Target gene symbol to test perturbation cascade on (e.g. 'GATA4', 'TP53', 'POU5F1')",
    )
    action: Optional[str] = Field(
        default="OVEREXPRESS",
        description="Perturbation action: 'OVEREXPRESS' or 'KNOCKOUT'",
    )
    desired_state: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional desired cellular state dict, e.g. {'CDKN2A': 'DOWN', 'MYH7': 'UP', 'COL1A1': 'DOWN'}",
    )


class GRNCausalResponse(BaseModel):
    cascade_analysis: Dict[str, Any]
    minimal_intervention_set: Optional[Dict[str, Any]]
    network_hubs: List[Dict[str, Any]]
    total_causal_tfs: int
    total_directed_edges: int
    summary: str


@router.post(
    "/causal-map",
    response_model=GRNCausalResponse,
    summary="Trace Causal Perturbation Cascade & Compute Minimal Intervention Set",
    description="""
Traces directed gene regulatory cascades through the Zenith Causal GRN (DAG)
and computes Minimal Intervention Sets (MIS) for cellular rejuvenation.

**Capabilities**:
- **Cascade Prediction**: Simulates downstream $N$-depth gene expression changes from KO/OE
- **DoRothEA/GENIE3 Integration**: Directed edges with confidence tiers (A/B)
- **Minimal Intervention Set (MIS)**: Solves for minimal TF set required to reach healthy state
    """,
)
async def causal_grn_map(request: GRNCausalRequest) -> GRNCausalResponse:
    try:
        result = run_causal_grn_map(
            target_gene=request.target_gene,
            action=request.action,
            desired_state=request.desired_state,
        )
        return GRNCausalResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Causal GRN mapping error: {str(e)}")


@router.get(
    "/causal-map/demo",
    summary="Demo: Trace GATA4 overexpression cascade & senescence MIS",
)
async def grn_demo() -> Dict[str, Any]:
    desired = {"CDKN2A": "DOWN", "MYH7": "UP", "COL1A1": "DOWN"}
    result = run_causal_grn_map(target_gene="GATA4", action="OVEREXPRESS", desired_state=desired)
    result["demo"] = True
    return result
