"""
Unit & Integration Tests for Cardiac-Specific Cellular Rejuvenation Engines (v31.0 GOLD)
Covers:
  - FerroAgingEngine (ACSL4/GPX4 lipid peroxidation auditing)
  - CardiacSafetyGate (TNNT2, MYH7, TTN, GJA1/Cx43 sarcomeric floors)
  - CardiacEnsembleClock (EnsembleAge + Krolevets 2026 ventricular heart failure clock)
"""

import sys
import os
import pytest

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ferro_aging_engine import get_ferro_aging_engine, FerroAgingEngine
from services.cardiac_safety_gate import get_cardiac_safety_gate, CardiacSafetyGate
from services.cardiac_ensemble_clock import get_cardiac_ensemble_clock, CardiacEnsembleClock


def test_ferro_aging_engine_baseline():
    engine = get_ferro_aging_engine()
    # Baseline healthy expression
    profile = {"ACSL4": 0.20, "GPX4": 0.85, "SLC7A11": 0.75, "FTH1": 0.80}
    res = engine.calculate_ferro_aging_index(profile)
    
    assert res["status"] in ["OPTIMAL_CYTOPROTECTION", "BALANCED_HOMEOSTASIS"]
    assert res["ferro_aging_index"] < 1.20
    assert res["protection_score_pct"] > 40.0
    assert "ACSL4" in res["literature_reference"]


def test_ferro_aging_engine_high_risk_trigger():
    engine = get_ferro_aging_engine()
    # High ACSL4 and low GPX4 (lipid peroxidation stress)
    profile = {"ACSL4": 0.95, "LPCAT3": 0.80, "GPX4": 0.15, "SLC7A11": 0.20, "FTH1": 0.20}
    res = engine.calculate_ferro_aging_index(profile)
    
    assert res["status"] == "HIGH_FERRO_AGING_RISK"
    assert res["risk_level"] == "HIGH"
    assert res["adjuvant_recommendation"] is not None
    assert "Liproxstatin" in res["adjuvant_recommendation"] or "Ascorbate" in res["adjuvant_recommendation"]


def test_cardiac_safety_gate_approved():
    gate = get_cardiac_safety_gate()
    factors = ["GATA4", "TBX5", "MEF2C"]
    res = gate.audit_cocktail_safety(factors, pulse_duration_hours=2.0)
    
    assert res["cardiac_clearance"] == "APPROVED"
    assert res["sarcomeric_retention_pct"] >= 80.0
    assert res["electrical_coupling_pct"] >= 80.0
    assert res["arrhythmia_risk_level"] in ["NEGLIGIBLE", "MODERATE"]


def test_cardiac_safety_gate_oncogene_violation():
    gate = get_cardiac_safety_gate()
    factors = ["MYC"] # High oncogenic hazard
    res = gate.audit_cocktail_safety(factors, pulse_duration_hours=2.0)
    
    assert res["cardiac_clearance"] == "RESCUE_REQUIRED"
    assert res["violations_detected"] > 0
    assert any(v["marker"] == "MYC" for v in res["violations_detail"])


def test_cardiac_ensemble_clock_absent_methylation():
    clock = get_cardiac_ensemble_clock()
    res = clock.predict_ensemble_age(methylation_betas=None, chronological_age=65.0)
    assert res["rejuvenation_delta_years"] is None
    assert res["status"] == "AWAITING_METHYLATION_ARRAY"
    assert res["periheart_lodo_mae_baseline_years"] == 6.97


def test_cardiac_ensemble_clock_with_betas():
    clock = get_cardiac_ensemble_clock()
    betas = {p: 0.50 for p in clock.horvath_service.coefficients.keys()}
    res = clock.predict_ensemble_age(
        methylation_betas=betas,
        chronological_age=65.0
    )
    
    assert res["ensemble_biological_age"] is not None
    assert len(res["ci_95_range"]) == 2
    assert "horvath_353_pan_tissue" in res["component_clocks"]
    assert "krolevets_ventricular_hf" in res["component_clocks"]
    assert "hannum_vascular_core" in res["component_clocks"]
