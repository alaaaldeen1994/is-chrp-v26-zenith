"""
AlphaZen RL Discovery Router — Zenith Phase 4
POST /api/v2/discovery/alphazen-optimize
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.alphazen_rl_engine import run_alphazen_optimization

router = APIRouter(prefix="/api/v2/discovery", tags=["AlphaZen RL Discovery Engine"])


class AlphaZenRequest(BaseModel):
    initial_cell_age_years: float = Field(
        default=65.0,
        ge=20.0,
        le=100.0,
        description="Baseline biological age of donor cells (years)",
    )
    target_cell_line: str = Field(
        default="iPSC-derived cardiomyocyte",
        description="Target cell lineage label",
    )
    n_rollout_episodes: int = Field(
        default=500,
        ge=50,
        le=5000,
        description="Number of Monte Carlo self-play policy rollouts",
    )
    max_cocktail_size: int = Field(
        default=4,
        ge=2,
        le=8,
        description="Maximum number of factors per cocktail",
    )


class AlphaZenResponse(BaseModel):
    search_parameters: Dict[str, Any]
    optimal_discovered_cocktail: Dict[str, Any]
    top_5_discovered_cocktails: List[Dict[str, Any]]
    summary: str


@router.post(
    "/alphazen-optimize",
    response_model=AlphaZenResponse,
    summary="Run AlphaZen RL Reprogramming Cocktail Discovery",
    description="""
Autonomous reinforcement learning (RL) self-play discovery engine for non-Yamanaka factor cocktails.

**RL Formulation**:
- **State Space**: 5,009 gene expression levels, Horvath clock biological age, cardiotoxicity risk score, oncogenic index
- **Action Space**: 36 transcription factors, 127 small molecule modulators, dosage adjustments
- **Reward Function**: $R = w_1 \Delta \text{Horvath} - w_2 \text{CardioRisk} - w_3 \text{OncoRisk} + w_4 \text{Yield}$
    """,
)
async def alphazen_optimize(request: AlphaZenRequest) -> AlphaZenResponse:
    try:
        result = run_alphazen_optimization(
            initial_cell_age_years=request.initial_cell_age_years,
            target_cell_line=request.target_cell_line,
            n_rollout_episodes=request.n_rollout_episodes,
            max_cocktail_size=request.max_cocktail_size,
        )
        return AlphaZenResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AlphaZen optimization error: {str(e)}")


@router.get(
    "/alphazen-optimize/demo",
    summary="Demo: Discover novel cardiac rejuvenation cocktail for 65yo cells",
)
async def alphazen_demo() -> Dict[str, Any]:
    result = run_alphazen_optimization(
        initial_cell_age_years=65.0,
        target_cell_line="iPSC-derived cardiomyocyte",
        n_rollout_episodes=300,
    )
    result["demo"] = True
    return result
