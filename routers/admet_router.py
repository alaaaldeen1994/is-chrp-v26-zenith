"""
ADMET Drug Safety Router — Zenith Phase 1
POST /api/v2/drug-design/admet-screen
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from services.admet_engine import run_admet_screen

router = APIRouter(prefix="/api/v2/drug-design", tags=["ADMET Drug Safety"])

THERAPEUTIC_AREAS = ["cardiac", "neurological", "oncology", "general", "metabolic", "immunology"]


class ADMETRequest(BaseModel):
    smiles: str = Field(
        ...,
        description="SMILES molecular string of drug candidate (e.g. 'CC(=O)Oc1ccccc1C(=O)O' for aspirin)",
        min_length=2,
        max_length=2000,
    )
    compound_name: str = Field(
        default="Unknown Compound",
        description="Human-readable compound name",
    )
    therapeutic_area: str = Field(
        default="cardiac",
        description="Therapeutic area: cardiac, neurological, oncology, general, metabolic, immunology",
    )


class ADMETResponse(BaseModel):
    compound: Dict[str, Any]
    molecular_properties: Dict[str, Any]
    lipinski_ro5: Dict[str, Any]
    veber_rules: Dict[str, Any]
    herg_cardiotoxicity: Dict[str, Any]
    cyp_inhibition: Dict[str, Any]
    bbb_permeability: Dict[str, Any]
    hepatotoxicity: Dict[str, Any]
    admet_grade: str
    admet_grade_justification: str
    structural_modification_suggestions: List[str]
    cardiac_specific_note: Optional[str]
    summary: str


@router.post(
    "/admet-screen",
    response_model=ADMETResponse,
    summary="ADMET Drug Safety Screening",
    description="""
Full pharmacokinetic and toxicity profiling of a drug candidate from its SMILES string.

**Implements**:
- **Lipinski Ro5**: MW ≤ 500 Da, logP ≤ 5, HBD ≤ 5, HBA ≤ 10
- **Veber rules**: Rotatable bonds ≤ 10, PSA ≤ 140 Å²
- **hERG cardiotoxicity**: Structural alert-based IC50 prediction (µM)
- **CYP3A4/2D6 inhibition**: Drug-drug interaction risk assessment
- **BBB permeability**: Clark model (PSA/MW/logP-based)
- **Hepatotoxicity**: Lhasa structural alert scanning
- **ADMET grade**: A/B/C/D/F composite safety grade

**Grade Scale**:
- A = Excellent (clinical candidate quality)
- B = Good (minor optimisation needed)
- C = Moderate (significant concerns)
- D = Poor (major liabilities)
- F = Fail (critical safety violations)
    """,
)
async def admet_screen(request: ADMETRequest) -> ADMETResponse:
    if request.therapeutic_area not in THERAPEUTIC_AREAS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid therapeutic_area '{request.therapeutic_area}'. Must be one of: {THERAPEUTIC_AREAS}",
        )

    try:
        result = run_admet_screen(
            smiles=request.smiles,
            compound_name=request.compound_name,
            therapeutic_area=request.therapeutic_area,
        )
        return ADMETResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ADMET screening error: {str(e)}")


@router.get(
    "/admet-screen/demo",
    summary="Demo: Screen aspirin and a known cardiotoxic compound",
    description="Returns ADMET profiles for aspirin (Grade A reference) and a hERG-active comparison.",
)
async def admet_demo() -> Dict[str, Any]:
    """Worked example comparing aspirin vs a hERG-active compound."""
    # Aspirin: CC(=O)Oc1ccccc1C(=O)O
    aspirin = run_admet_screen(
        smiles="CC(=O)Oc1ccccc1C(=O)O",
        compound_name="Aspirin",
        therapeutic_area="cardiac",
    )
    # E-4031 (known hERG blocker): simplified SMILES
    herg_compound = run_admet_screen(
        smiles="CCN1CCN(CCc2ccc(NS(=O)(=O)c3ccc(N)cc3)cc2)CC1",
        compound_name="E-4031 (hERG reference blocker)",
        therapeutic_area="cardiac",
    )
    return {
        "demo": True,
        "description": "ADMET comparison: Aspirin (reference) vs E-4031 (hERG positive control)",
        "aspirin_profile": aspirin,
        "herg_compound_profile": herg_compound,
    }


@router.get(
    "/admet-screen/grade-scale",
    summary="ADMET grade scale explanation",
)
async def admet_grade_scale() -> Dict[str, Any]:
    return {
        "grade_scale": {
            "A": "Excellent ADMET — all properties in optimal ranges, clinical candidate quality",
            "B": "Good — 1 minor property concern, optimisable",
            "C": "Moderate — 2-3 concerns, requires lead optimisation",
            "D": "Poor — significant PK or safety liabilities",
            "F": "FAIL — critical violations (hERG IC50 < 1µM, multiple Ro5 failures, severe hepatotox)",
        },
        "key_thresholds": {
            "MW_optimal_Da": "≤ 500",
            "logP_optimal": "-1 to 5",
            "HBD_max": 5,
            "HBA_max": 10,
            "PSA_oral_max_angstrom2": 140,
            "hERG_safe_IC50_uM": "> 30",
            "hERG_flagged_IC50_uM": "< 5",
            "hERG_critical_IC50_uM": "< 1",
        },
        "sources": [
            "Lipinski et al. (2001) Advanced Drug Delivery Reviews 46:3-26",
            "Veber et al. (2002) Journal of Medicinal Chemistry 45:2615-2623",
            "Ertl et al. (2000) Journal of Medicinal Chemistry 43:3714-3717",
        ],
    }
