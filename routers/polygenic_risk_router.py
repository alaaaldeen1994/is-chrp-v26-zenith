"""
Polygenic Risk Score Router — Zenith Phase 1
POST /api/v2/genomics/polygenic-risk
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.polygenic_risk_engine import run_prs_analysis

router = APIRouter(prefix="/api/v2/genomics", tags=["Polygenic Risk Score"])


class VariantInput(BaseModel):
    rsid: str = Field(..., description="dbSNP rsID (e.g. rs2234962)")
    chromosome: str = Field(default="unknown", description="Chromosome (e.g. '12')")
    position: int = Field(default=0, description="Genomic position (1-based, GRCh38)")
    ref_allele: str = Field(default="A", description="Reference allele")
    alt_allele: str = Field(default="G", description="Alternate allele")
    genotype: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Allele dosage: 0=homozygous ref, 1=heterozygous, 2=homozygous alt",
    )
    maf: float = Field(default=0.05, ge=0.0, le=1.0, description="Minor allele frequency")


class PRSRequest(BaseModel):
    variants: List[VariantInput] = Field(
        ...,
        min_items=1,
        max_items=500,
        description="List of patient genomic variants",
    )
    phenotype: str = Field(
        default="Cardiomyopathy",
        description="Target disease phenotype for contextualisation",
    )
    cell_type: str = Field(
        default="iPSC-derived cardiomyocyte",
        description="Cell type context for CRISPR recommendations",
    )


class PRSResponse(BaseModel):
    additive_prs: float
    epistatic_prs: float
    combined_prs: float
    percentile: float
    risk_category: str
    horvath_age_acceleration_years: float
    matched_variants: List[Dict[str, Any]]
    epistatic_pairs: List[Dict[str, Any]]
    top_causal_variants: List[Dict[str, Any]]
    crispr_correction_priority: List[Dict[str, Any]]
    summary: str
    statistics: Dict[str, Any]


@router.post(
    "/polygenic-risk",
    response_model=PRSResponse,
    summary="Compute Polygenic Risk Score (PRS)",
    description="""
Computes additive and epistatic PRS from patient genomic variants.

**Additive model**: PRS = Σ(beta_i × G_i)
**Epistatic model**: PRS_epi = additive + Σ(gamma_ij × G_i × G_j)

The epistatic interaction coefficients gamma_ij are derived from the
Zenith 5,009-gene GRN co-expression matrix, grounding epistatic scores
in real biological regulatory networks.

**Output includes**:
- Combined PRS score (percentile vs UK Biobank population)
- Epistatic gene interaction pairs (from GRN)
- Horvath epigenetic clock acceleration estimate (years)
- Top 5 causal variant pairs with interaction coefficients
- CRISPR correction priority ranking with editor recommendation
    """,
)
async def compute_polygenic_risk(request: PRSRequest) -> PRSResponse:
    try:
        variants_payload = [v.dict() for v in request.variants]
        result = run_prs_analysis(
            variants_payload=variants_payload,
            phenotype=request.phenotype,
            cell_type=request.cell_type,
        )
        return PRSResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PRS computation error: {str(e)}")


@router.get(
    "/polygenic-risk/demo",
    summary="Demo: Cardiac PRS for example patient",
    description="Returns a worked example using cardiac disease variants from the GWAS catalog.",
)
async def prs_demo() -> Dict[str, Any]:
    """Pre-computed demo using 4 cardiac risk variants."""
    demo_variants = [
        {"rsid": "rs2234962",  "chromosome": "14", "position": 23397721, "ref_allele": "G", "alt_allele": "C", "genotype": 1, "maf": 0.04},
        {"rsid": "rs11107116", "chromosome": "8",  "position": 11600000, "ref_allele": "T", "alt_allele": "A", "genotype": 1, "maf": 0.03},
        {"rsid": "rs3729547",  "chromosome": "1",  "position": 156100000,"ref_allele": "C", "alt_allele": "T", "genotype": 2, "maf": 0.01},
        {"rsid": "rs10936599", "chromosome": "3",  "position": 169773939, "ref_allele": "T", "alt_allele": "C", "genotype": 1, "maf": 0.03},
    ]
    result = run_prs_analysis(demo_variants, phenotype="Cardiomyopathy + Aging", cell_type="iPSC-derived cardiomyocyte")
    result["demo"] = True
    result["note"] = "Example patient carrying MYH7, GATA4, LMNA, and TERC risk variants"
    return result
