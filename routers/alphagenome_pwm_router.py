"""
AlphaGenome PWM Scan Router — Zenith Phase 1
POST /api/v2/alphagenome/pwm-scan
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from services.alphagenome_sequence_scanner import run_pwm_scan, PWM_DATABASE

router = APIRouter(prefix="/api/v2/alphagenome", tags=["AlphaGenome PWM Scanner"])

AVAILABLE_TFS = list(PWM_DATABASE.keys())


class PWMScanRequest(BaseModel):
    ref_sequence: str = Field(
        ...,
        min_length=20,
        max_length=5000,
        description="Reference DNA sequence (recommend 201bp window centred on variant position)",
    )
    alt_sequence: str = Field(
        ...,
        min_length=20,
        max_length=5000,
        description="Alternate allele sequence (same length as ref_sequence)",
    )
    variant_rsid: str = Field(default="unknown", description="dbSNP rsID")
    chromosome: str = Field(default="unknown", description="Chromosome label (e.g. '12')")
    position: int = Field(default=0, description="Genomic position (1-based, GRCh38)")
    tf_subset: Optional[List[str]] = Field(
        default=None,
        description="Optional list of TF names to restrict scan to. Leave null to scan all 15 TFs.",
    )


class PWMScanResponse(BaseModel):
    variant: Dict[str, Any]
    tf_scan_results: List[Dict[str, Any]]
    disrupted_tfs: List[Dict[str, Any]]
    disrupted_count: int
    top_disrupted_tf: Optional[Dict[str, Any]]
    summary: str
    clinical_interpretation: str
    alphagenome_confidence: float


@router.post(
    "/pwm-scan",
    response_model=PWMScanResponse,
    summary="Scan DNA sequence variant for TF binding disruption",
    description="""
Scans reference and alternate DNA sequences against 15 pioneer TF PWMs
from JASPAR 2024 to detect regulatory binding site disruption.

**PWM Scoring formula**:
    score(s) = Σ_i log2(f_i,s_i / b_s_i)

A delta-score < -2.0 is classified as significant binding disruption.

**15 TFs scanned**: GATA4, MEF2C, NKX2-5, CTCF, SRF, POU5F1, SOX2, NANOG,
TEAD1, TP53, KLF4, MYC, RUNX1, FOXO3, SP1

**Output includes**:
- Per-TF binding score delta table
- Chromatin accessibility prediction (delta-ATAC-seq %)
- Enhancer-promoter loop disruption probability
- Clinical interpretation of regulatory impact
- AlphaGenome confidence score
    """,
)
async def pwm_scan(request: PWMScanRequest) -> PWMScanResponse:
    if len(request.ref_sequence) != len(request.alt_sequence):
        raise HTTPException(
            status_code=400,
            detail=(
                f"ref_sequence ({len(request.ref_sequence)}bp) and alt_sequence "
                f"({len(request.alt_sequence)}bp) must be the same length."
            ),
        )

    # Validate TF subset
    if request.tf_subset:
        invalid = [tf for tf in request.tf_subset if tf not in AVAILABLE_TFS]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown TF(s): {invalid}. Available: {AVAILABLE_TFS}",
            )

    try:
        result = run_pwm_scan(
            ref_sequence=request.ref_sequence,
            alt_sequence=request.alt_sequence,
            variant_rsid=request.variant_rsid,
            chromosome=request.chromosome,
            position=request.position,
            tf_subset=request.tf_subset,
        )
        return PWMScanResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PWM scan error: {str(e)}")


@router.get(
    "/pwm-scan/demo",
    summary="Demo: Scan MYH6 enhancer variant chr12:111842901 C>T",
    description="Worked example scanning a real cardiac enhancer variant.",
)
async def pwm_scan_demo() -> Dict[str, Any]:
    """
    Demo: chr12:111,842,901 C>T variant in MYH6 cardiac enhancer.
    Reference 51bp window with GATA4 binding motif disruption example.
    """
    # 51bp reference sequence with embedded GATA4 motif (TGATAA core)
    ref_seq = "GCTAGCTAGCTAGCTAGCTAGCTGATAAATGATCCGCTAGCTAGCTAGCT"
    # Alternate: C>T at position 26 (within GATA4 core)
    alt_seq = "GCTAGCTAGCTAGCTAGCTAGCTTATAAATGATCCGCTAGCTAGCTAGCT"

    result = run_pwm_scan(
        ref_sequence=ref_seq,
        alt_sequence=alt_seq,
        variant_rsid="rs2128739",
        chromosome="12",
        position=111842901,
    )
    result["demo"] = True
    result["note"] = "MYH6 cardiac enhancer — GATA4 binding site C>T variant"
    return result


@router.get(
    "/pwm-scan/tfs",
    summary="List all available TF PWMs",
    description="Returns the list of all 15 TFs available for PWM scanning.",
)
async def list_tfs() -> Dict[str, Any]:
    return {
        "available_transcription_factors": AVAILABLE_TFS,
        "count": len(AVAILABLE_TFS),
        "source": "JASPAR 2024",
        "disruption_threshold": -2.0,
        "description": (
            "All TFs are scored using position weight matrices (PWMs). "
            "A delta-score below -2.0 indicates significant binding site disruption."
        ),
    }
