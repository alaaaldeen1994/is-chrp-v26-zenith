"""
Structural Protein-Drug Docking Router — Zenith Phase 3
POST /api/v2/drug-design/docking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple

from services.docking_engine import run_docking_simulation

router = APIRouter(prefix="/api/v2/drug-design", tags=["Structural Protein-Drug Docking"])


class DockingRequest(BaseModel):
    target_protein: str = Field(
        default="GATA4",
        description="Target protein name (e.g. 'GATA4', 'MYH7', 'TP53')",
    )
    pdb_id: Optional[str] = Field(
        default="P43694",
        description="PDB accession or AlphaFold ID",
    )
    ligand_smiles: str = Field(
        default="CC(=O)Oc1ccccc1C(=O)O",
        description="SMILES string of ligand drug candidate",
    )
    ligand_name: str = Field(
        default="Candidate_001",
        description="Ligand human-readable name",
    )
    center_xyz: Tuple[float, float, float] = Field(
        default=(12.5, 45.2, -8.1),
        description="Grid box center coordinates (X, Y, Z in Angstroms)",
    )
    box_size_xyz: Tuple[float, float, float] = Field(
        default=(20.0, 20.0, 20.0),
        description="Grid box dimensions (X, Y, Z in Angstroms)",
    )


class DockingResponse(BaseModel):
    docking_job: Dict[str, Any]
    binding_affinity: Dict[str, Any]
    key_binding_interactions: List[str]
    off_target_selectivity_screen: Dict[str, Any]
    summary: str


@router.post(
    "/docking",
    response_model=DockingResponse,
    summary="Run Structural Protein-Drug Docking Simulation",
    description="""
Performs grid-based molecular docking and binding free energy estimation ($\Delta G_{bind}$)
using an AutoDock Vina-like semi-empirical force field.

**Outputs**:
- $\Delta G_{bind}$ in kcal/mol
- Predicted $K_d$ and $IC_{50}$ (Cheng-Prusoff equation)
- Key hydrogen bonding and van der Waals interactions
- 8-protein off-target selectivity screening
- Selectivity Index calculation
    """,
)
async def docking(request: DockingRequest) -> DockingResponse:
    try:
        result = run_docking_simulation(
            target_protein=request.target_protein,
            pdb_id=request.pdb_id,
            ligand_smiles=request.ligand_smiles,
            ligand_name=request.ligand_name,
            center_xyz=request.center_xyz,
            box_size_xyz=request.box_size_xyz,
        )
        return DockingResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docking simulation error: {str(e)}")


@router.get(
    "/docking/demo",
    summary="Demo: Dock small molecule against GATA4 transcription factor",
)
async def docking_demo() -> Dict[str, Any]:
    result = run_docking_simulation(
        target_protein="GATA4",
        pdb_id="P43694",
        ligand_smiles="CC(=O)Oc1ccccc1C(=O)O",
        ligand_name="GATA4_Activator_Demo",
    )
    result["demo"] = True
    return result
