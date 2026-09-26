import sys
import os

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.multiomics_service import MultiOmicsPredictorService
from services.pkpd_engine import PKPDEngine

def test_pkpd_dynamics():
    # Verify PK/PD unapproved drug dosing engine is decommissioned
    time_pts, tissue_conc, avg_conc = PKPDEngine.simulate_dosing("compound", 1.0, 24.0, duration_days=14)
    assert time_pts == []
    assert tissue_conc == []
    assert avg_conc == 0.0

def test_perturbation_trajectory():
    service = MultiOmicsPredictorService()
    res = service.predict_perturbation_trajectory("fibroblast", {"GATA4": 1.0})
    assert res["status"] in ["CONVERGED", "success"]
    assert "transcriptomic_stability" in res
    assert "syncytial_safety_index" in res
    assert "expression_profiles" in res

if __name__ == "__main__":
    print("Running sanitized mechanistic v30 tests...")
    test_pkpd_dynamics()
    test_perturbation_trajectory()
    print("All mechanistic v30 tests passed successfully!")
