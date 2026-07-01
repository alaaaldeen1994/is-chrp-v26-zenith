from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class LNPOptimizeRequest(BaseModel):
    molar_ratios: Dict[str, float] = Field(
        ..., 
        example={"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
        description="Molar percentages of ionizable, helper, cholesterol, and PEG lipids (must sum to 1.0)"
    )
    np_ratio: float = Field(..., ge=1.0, le=20.0, description="Nitrogen-to-Phosphate molar ratio")
    active_ligand_conjugation: bool = Field(False, description="Whether active targeting ligands are conjugated to the surface")
    ligand_density: float = Field(0.0, ge=0.0, le=10.0, description="Percentage density of targeted surface ligands")
    peg_mw: float = Field(2000.0, description="Molecular weight of PEG lipids (usually 2000 Da)")

class PerturbationRequest(BaseModel):
    baseline_cell_type: str = Field("ventricular_myocyte", description="Cell type: fibroblast, ventricular_myocyte, endo, etc.")
    perturbation_factors: Dict[str, float] = Field(
        ..., 
        example={"GATA4": 1.0, "SIRT1": 2.0},
        description="Map of candidate gene symbols or compounds and their dosage/activation level"
    )
    census_filter: Optional[str] = Field(None, example="tissue_general == 'heart' and disease == 'normal'", description="Chan Zuckerberg Cellxgene Census query filter to extract baseline cell profiles")

class SafetyAuditRequest(BaseModel):
    factors: List[str] = Field(..., example=["GATA4", "TBX5", "OCT4"], description="List of gene symbols to evaluate for safety")
    cpg_methylation: Optional[Dict[str, float]] = Field(None, example={"cg00000292": 0.45, "cg00050873": 0.12}, description="Map of CpG site probe IDs and their methylation beta-values")

class DiscoveryRequest(BaseModel):
    target_query: str = Field(..., example="cardiac myocyte rejuvenation", description="Text description of the desired cell state transition")
    cell_type: str = Field("ventricular_myocyte", description="Cell type to perform candidate factor discovery on")
    safety_level: Optional[str] = Field("balanced", description="Safety threshold: conservative, balanced, aggressive")

class VirtualTrialRequest(BaseModel):
    disease: str = Field(..., example="HFpEF", description="Target disease condition (e.g. HFpEF, HFrEF, general_aging)")
    protocol: str = Field("NMN_daily", description="Target therapeutic protocol description")
    cohort_size: int = Field(100, ge=10, le=1000, description="Number of virtual digital twins to simulate")
    variance: float = Field(0.1, ge=0.0, le=1.0, description="Stochastic biological variance across cohort")
    nmn_dosage: float = Field(500.0, description="Dosage of NMN in mg")
    oral_administration: bool = Field(True, description="Whether compound is orally administered (applies gut deamidation penalty)")

class ProteinFoldingRequest(BaseModel):
    sequence: str = Field(..., min_length=5, max_length=2048, example="MAPL...", description="Amino acid sequence (5-2048 letters) to fold into 3D atomic coordinates")
