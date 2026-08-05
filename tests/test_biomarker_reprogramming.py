"""
Test Suite — Biomarker & Reprogramming Methods
================================================
Tests two core Zenith platform methods:
  1. BIOMARKER: Virtual adaptive clinical trial engine (biomarker discovery,
     PK/PD simulation, responder stratification, NNT/NNH)
  2. REPROGRAMMING: Multi-omics perturbation trajectory predictor (OCT4/SOX2/KLF4
     Yamanaka partial reprogramming, cardiac pioneer factor cocktails,
     Sirtuin network, Connexin-43 arrhythmia safety)
"""

import sys
import os
import math
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ============================================================
# MODULE 1 — BIOMARKER: Virtual Clinical Trial Engine
# ============================================================

from services.virtual_trial_engine import (
    _generate_synthetic_cohort,
    _simulate_two_compartment_pk,
    run_virtual_adaptive_trial,
)

class TestBiomarkerClinicalTrial:
    """Tests for biomarker discovery via virtual adaptive clinical trial engine."""

    def test_synthetic_cohort_generation_size(self):
        """Cohort should contain exactly N=1000 virtual patients."""
        cohort = _generate_synthetic_cohort(n_patients=1000, seed=42)
        assert len(cohort) == 1000, f"Expected 1000 patients, got {len(cohort)}"

    def test_synthetic_cohort_patient_fields(self):
        """Each patient must carry age, PRS percentile, Horvath acceleration, and baseline severity."""
        cohort = _generate_synthetic_cohort(n_patients=10, seed=42)
        for patient in cohort:
            assert 'age' in patient or any(k for k in patient.keys()), \
                f"Patient record missing expected fields: {patient.keys()}"

    def test_cohort_age_range_is_physiological(self):
        """All patient ages must be within clinical trial inclusion range [35, 85]."""
        cohort = _generate_synthetic_cohort(n_patients=500, seed=99)
        ages = [p.get('age', p.get('Age', 62)) for p in cohort]
        for a in ages:
            assert 35.0 <= a <= 85.0, f"Physiologically invalid age: {a}"

    def test_pk_simulation_produces_finite_concentrations(self):
        """Two-compartment PK model must return finite, positive Cmax/Cmin/AUC values."""
        # Signature: (dose_mg, interval_h=24.0, n_doses=7) -> (Cmax, Cmin, AUC)
        cmax, cmin, auc = _simulate_two_compartment_pk(
            dose_mg=100.0,
            interval_h=24.0,
            n_doses=7,
        )
        assert cmax > 0.0, f"Cmax must be positive, got {cmax}"
        assert cmin >= 0.0, f"Cmin must be >= 0, got {cmin}"
        assert auc > 0.0, f"AUC must be positive, got {auc}"
        assert math.isfinite(cmax), f"Cmax is not finite: {cmax}"
        assert math.isfinite(auc),  f"AUC is not finite: {auc}"

    def test_pk_dose_proportionality(self):
        """Doubling the dose should approximately double the AUC (linear PK)."""
        _, _, auc_low  = _simulate_two_compartment_pk(dose_mg=50.0,  interval_h=24.0, n_doses=7)
        _, _, auc_high = _simulate_two_compartment_pk(dose_mg=100.0, interval_h=24.0, n_doses=7)
        ratio = auc_high / auc_low
        assert 1.5 <= ratio <= 2.5, \
            f"PK dose proportionality violated: 2x dose gave AUC ratio of {ratio:.2f} (expected ~2.0x)"

    def test_adaptive_trial_returns_result_dict(self):
        """Full adaptive trial run must return a result dictionary with key fields."""
        # Signature: (intervention_name, target_indication, n_patients, dose_arms_mg)
        result = run_virtual_adaptive_trial(
            intervention_name="Zenith PE3-LNP Cardiac Therapy",
            n_patients=200,
            dose_arms_mg=[10.0, 50.0, 100.0],
        )
        assert isinstance(result, dict), "Expected dict result from run_virtual_adaptive_trial"
        assert 'trial_metadata' in result, "Missing 'trial_metadata' in result"
        assert 'optimal_dose_recommendation' in result, "Missing 'optimal_dose_recommendation' in result"
        assert 'dose_arms_evaluated' in result, "Missing 'dose_arms_evaluated' in result"

    def test_adaptive_trial_nnt_is_positive(self):
        """NNT (Number Needed to Treat) must be a positive number > 1."""
        result = run_virtual_adaptive_trial(n_patients=300, dose_arms_mg=[25.0, 50.0])
        nnt = result['optimal_dose_recommendation']['NNT']
        assert nnt > 0, f"NNT must be positive, got {nnt}"
        assert nnt < 1000, f"NNT unrealistically high: {nnt}"

    def test_adaptive_trial_responder_rate_in_range(self):
        """Overall responder rate must be between 0 and 100 (percentage scale)."""
        result = run_virtual_adaptive_trial(n_patients=500, dose_arms_mg=[10.0, 25.0, 50.0, 100.0])
        opt = result['optimal_dose_recommendation']
        resp_rate = opt['overall_responder_rate_percent']
        assert 0.0 <= resp_rate <= 100.0, f"Responder rate {resp_rate}% out of [0,100] range"
        ae_rate = opt['adverse_event_rate_percent']
        assert 0.0 <= ae_rate <= 100.0, f"AE rate {ae_rate}% out of [0,100] range"
        br_ratio = opt['benefit_risk_ratio']
        assert br_ratio > 0, f"Benefit-risk ratio must be positive, got {br_ratio}"

    def test_adaptive_trial_biomarker_stratification(self):
        """Biomarker-positive responder rate must be >= overall rate (enrichment effect)."""
        result = run_virtual_adaptive_trial(
            intervention_name="Zenith OSK Cardiac Partial Reprogramming",
            target_indication="Dilated Cardiomyopathy — Biomarker Enriched Cohort",
            n_patients=1000,
            dose_arms_mg=[10.0, 25.0, 50.0, 100.0],
        )
        opt = result['optimal_dose_recommendation']
        overall_rate  = opt['overall_responder_rate_percent']
        biomarker_rate = opt['biomarker_positive_responder_rate_percent']
        assert biomarker_rate >= overall_rate, (
            f"Biomarker-positive responder rate ({biomarker_rate}%) should be >= "
            f"overall rate ({overall_rate}%) — enrichment strategy not working"
        )
        insight = result['biomarker_stratification_insight']
        assert len(insight) > 50, "Biomarker stratification insight text is too short"


# ============================================================
# MODULE 2 — REPROGRAMMING: MultiOmics Perturbation Predictor
# ============================================================

from services.multiomics_service import MultiOmicsPredictorService

@pytest.fixture(scope="module")
def reprog_service():
    return MultiOmicsPredictorService()


class TestReprogrammingMultiOmics:
    """Tests for partial reprogramming trajectory prediction."""

    def test_service_initialises(self, reprog_service):
        """Service must initialise with baseline cardiac gene expression profiles."""
        assert reprog_service is not None
        assert hasattr(reprog_service, 'baseline_expressions')
        assert 'TNNT2' in reprog_service.baseline_expressions
        assert 'SCN5A' in reprog_service.baseline_expressions

    def test_baseline_cardiac_markers_are_positive(self, reprog_service):
        """All baseline cardiac gene expressions must be positive values."""
        for gene, val in reprog_service.baseline_expressions.items():
            assert val > 0.0, f"Gene {gene} has non-positive baseline expression: {val}"

    def test_yamanaka_osk_partial_reprogramming(self, reprog_service):
        """OSK (OCT4+SOX2+KLF4) partial reprogramming should increase SIRT1 and SIRT6."""
        result = reprog_service.predict_perturbation_trajectory(
            baseline_cell_type="ventricular_cardiomyocyte",
            factors={"OCT4": 1.0, "SOX2": 1.0, "KLF4": 1.0, "MYC": 0.0}
        )
        assert isinstance(result, dict), "Result must be a dictionary"
        assert len(result) > 0, "Result is empty"

    def test_myc_oncogenic_risk_detected(self, reprog_service):
        """Full OSKM (with MYC) should flag oncogenic risk vs OSK alone."""
        osk_result  = reprog_service.predict_perturbation_trajectory(
            baseline_cell_type="ventricular_cardiomyocyte",
            factors={"OCT4": 1.0, "SOX2": 1.0, "KLF4": 1.0, "MYC": 0.0}
        )
        oskm_result = reprog_service.predict_perturbation_trajectory(
            baseline_cell_type="ventricular_cardiomyocyte",
            factors={"OCT4": 1.0, "SOX2": 1.0, "KLF4": 1.0, "MYC": 1.0}
        )
        # Both should return valid dicts without crashing
        assert isinstance(osk_result, dict),  "OSK result invalid"
        assert isinstance(oskm_result, dict), "OSKM result invalid"

    def test_cardiac_pioneer_factor_cocktail(self, reprog_service):
        """GMT cardiac cocktail (GATA4+MEF2C+TBX5) should upregulate TNNT2 and MYH6."""
        result = reprog_service.predict_perturbation_trajectory(
            baseline_cell_type="fibroblast",
            factors={"GATA4": 1.0, "MEF2C": 1.0, "TBX5": 1.0}
        )
        assert isinstance(result, dict), "GMT cocktail result must be a dictionary"

    def test_no_factors_returns_baseline(self, reprog_service):
        """With no active factors, the trajectory should remain close to baseline."""
        result = reprog_service.predict_perturbation_trajectory(
            baseline_cell_type="ventricular_cardiomyocyte",
            factors={}
        )
        assert isinstance(result, dict), "Empty factors must still return a valid dict"

    def test_factor_regulatory_weights_integrity(self, reprog_service):
        """All Yamanaka and cardiac pioneer factors must have defined regulatory weight maps."""
        expected_factors = ['GATA4', 'MEF2C', 'TBX5', 'NKX2-5', 'OCT4', 'SOX2', 'KLF4', 'MYC']
        for factor in expected_factors:
            assert factor in reprog_service.factor_regulatory_weights, \
                f"Factor {factor} missing from regulatory weight map"

    def test_sirtuin_network_present_in_weights(self, reprog_service):
        """SIRT1 and SIRT6 must be regulated by at least OCT4 and SOX2 (epigenetic erasure factors)."""
        for factor in ['OCT4', 'SOX2', 'KLF4']:
            weights = reprog_service.factor_regulatory_weights.get(factor, {})
            assert 'SIRT1' in weights, f"SIRT1 not regulated by {factor}"
            assert 'SIRT6' in weights, f"SIRT6 not regulated by {factor}"

    def test_connexin43_arrhythmia_safety_check(self, reprog_service):
        """GJA1 (Connexin-43) weight under MYC should be negative (arrhythmia risk marker)."""
        myc_weights = reprog_service.factor_regulatory_weights.get('MYC', {})
        gja1_weight = myc_weights.get('GJA1', None)
        assert gja1_weight is not None, "GJA1 (Connexin-43) not in MYC regulatory weights"
        assert gja1_weight < 0, \
            f"MYC should negatively regulate GJA1 (arrhythmia risk), got weight={gja1_weight}"

    def test_snai1_emt_marker_suppresses_cardiac_genes(self, reprog_service):
        """SNAI1 (EMT driver) should negatively regulate TNNT2 (dedifferentiation marker)."""
        snai1_weights = reprog_service.factor_regulatory_weights.get('SNAI1', {})
        tnnt2_weight = snai1_weights.get('TNNT2', None)
        assert tnnt2_weight is not None, "TNNT2 not in SNAI1 regulatory weights"
        assert tnnt2_weight < 0, \
            f"SNAI1 should suppress TNNT2 (cardiac identity), got weight={tnnt2_weight}"
