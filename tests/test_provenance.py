"""
Provenance Test Suite — Zenith Platform Integrity
===================================================
Validates:
  1. Complete quarantine of rigged screening pipelines and fabricated CSV outputs.
  2. Decommissioning (HTTP 410) of ungrounded endpoints.
  3. Integrity of calibrated real assets (HCA atlas genes, real structure folding).
  4. Absence of hardcoded drug dosing and synthetic clock shifts.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_quarantined_files_not_in_root():
    """Verify legacy rigged screening pipelines and CSV outputs are quarantined."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    banned_root_files = [
        "run_zenith_screening_pipeline.py",
        "zenith_screening_audit.csv",
        "screen_output.csv",
        "validation_outputs/part2_real_screen/screen_output.csv"
    ]
    for rel_path in banned_root_files:
        full_path = os.path.join(repo_root, rel_path)
        assert not os.path.exists(full_path), f"Quarantined file still exists in root: {rel_path}"

    # Verify they exist in quarantine
    assert os.path.exists(os.path.join(repo_root, "quarantine", "track2", "run_zenith_screening_pipeline.py"))


def test_drug_dosing_pkpd_decommissioned():
    """Verify prescription drug dosing panel and PK models are decommissioned."""
    from services.pkpd_engine import PKPDEngine
    time_pts, conc, avg = PKPDEngine.simulate_dosing("compound", 1.0, 24.0)
    assert time_pts == []
    assert conc == []
    assert avg == 0.0


def test_structural_folder_no_synthetic_fallback():
    """Verify synthetic fallback PDB generation is strictly disabled."""
    from config.settings import settings
    from services.structural_folder import StructuralFolderService
    
    assert settings.ESMFOLD_FALLBACK_ENABLED is False
    folder = StructuralFolderService()
    with pytest.raises(RuntimeError):
        folder._generate_fallback_pdb("MKLLVLSLSL", reason="testing")


def test_cardiac_ensemble_clock_provenance():
    """Verify cardiac ensemble clock requires empirical methylation and returns None when absent."""
    from services.cardiac_ensemble_clock import get_cardiac_ensemble_clock
    clock = get_cardiac_ensemble_clock()
    
    res = clock.predict_ensemble_age(methylation_betas=None, chronological_age=65.0)
    assert res["rejuvenation_delta_years"] is None
    assert res["status"] == "AWAITING_METHYLATION_ARRAY"
    assert res["periheart_lodo_mae_baseline_years"] == 6.97


def test_decommissioned_endpoint_definitions():
    """Verify endpoint routers return HTTP 410 for decommissioned routes."""
    from routers.neural_router import dual_age_assessment
    from routers.multiomics_router import integrate_multiomics, MultiOmicsRequest
    from routers.api_v1 import post_predict_perturbation, post_safety_audit, post_trials_run
    from fastapi import HTTPException
    import asyncio

    # neural router dual endpoint
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dual_age_assessment(None))
    assert exc.value.status_code == 410

    # multiomics router integrate
    with pytest.raises(HTTPException) as exc:
        asyncio.run(integrate_multiomics(MultiOmicsRequest()))
    assert exc.value.status_code == 410

    # api_v1 perturbation
    with pytest.raises(HTTPException) as exc:
        post_predict_perturbation()
    assert exc.value.status_code == 410

    # api_v1 safety audit
    with pytest.raises(HTTPException) as exc:
        post_safety_audit()
    assert exc.value.status_code == 410

    # api_v1 virtual trial run
    with pytest.raises(HTTPException) as exc:
        post_trials_run()
    assert exc.value.status_code == 410

    # api_v1 structure fold
    from routers.api_v1 import post_structure_fold
    with pytest.raises(HTTPException) as exc:
        post_structure_fold()
    assert exc.value.status_code == 410

