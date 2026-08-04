"""
Mendelian Randomisation Router — Zenith Phase 2
POST /api/v2/causal/mendelian-randomisation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.mendelian_randomisation_engine import run_mendelian_randomisation

router = APIRouter(prefix="/api/v2/causal", tags=["Causal Inference — Mendelian Randomisation"])


class SNPInstrumentInput(BaseModel):
    rsid: str = Field(..., description="dbSNP rsID")
    beta_X: float = Field(..., description="Effect size of SNP on exposure X")
    se_X: float = Field(..., description="Standard error of beta_X")
    beta_Y: float = Field(..., description="Effect size of SNP on outcome Y")
    se_Y: float = Field(..., description="Standard error of beta_Y")
    effect_allele: str = Field(default="A", description="Effect allele")


class MRRequest(BaseModel):
    exposure: str = Field(
        ...,
        description="Exposure variable (e.g. 'GATA4_expression', 'Telomere_length', 'TP53_senescence_axis')",
    )
    outcome: str = Field(
        ...,
        description="Outcome phenotype (e.g. 'Epigenetic_Age_Acceleration', 'Cardiomyopathy_Risk')",
    )
    custom_instruments: Optional[List[SNPInstrumentInput]] = Field(
        default=None,
        description="Optional list of custom instrument SNPs. If omitted, Zenith lookup catalog is used.",
    )


class MRResponse(BaseModel):
    study: Dict[str, Any]
    instrument_strength: Dict[str, Any]
    ivw_mr_results: Dict[str, Any]
    mr_egger_pleiotropy_test: Dict[str, Any]
    weighted_median_mr: Dict[str, Any]
    directionality_steiger_test: Dict[str, Any]
    causal_verdict: str
    summary: str


@router.post(
    "/mendelian-randomisation",
    response_model=MRResponse,
    summary="Run Mendelian Randomisation Causal Inference",
    description="""
Establishes unconfounded causal relationships between molecular exposures and biological outcomes.

**Estimators included**:
- **IVW (Inverse-Variance Weighted)**: Standard causal effect estimate $\\beta_{IVW}$
- **MR-Egger Regression**: Detects horizontal pleiotropy via non-zero intercept test
- **Weighted Median**: Robust to up to 50% invalid instrument SNPs
- **Steiger Test**: Proves causal directionality ($X \\rightarrow Y$ vs $Y \\rightarrow X$)
- **Instrument Validation**: F-statistic $> 10$ strength test
    """,
)
async def mendelian_randomisation(request: MRRequest) -> MRResponse:
    try:
        custom_inst = [i.dict() for i in request.custom_instruments] if request.custom_instruments else None
        result = run_mendelian_randomisation(
            exposure=request.exposure,
            outcome=request.outcome,
            custom_instruments=custom_inst,
        )
        return MRResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mendelian Randomisation error: {str(e)}")


@router.get(
    "/mendelian-randomisation/demo",
    summary="Demo: GATA4 expression -> Epigenetic Age Acceleration MR study",
    description="Pre-computed Mendelian Randomisation study demonstrating GATA4 causal impact on Horvath clock age.",
)
async def mr_demo() -> Dict[str, Any]:
    result = run_mendelian_randomisation(
        exposure="GATA4_expression",
        outcome="Epigenetic_Age_Acceleration",
    )
    result["demo"] = True
    return result
