import sys
import os

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.multiomics_service import MultiOmicsPredictorService

def test_multiomics_cardiac_cocktail():
    service = MultiOmicsPredictorService()
    factors = {"GATA4": 1.0, "MEF2C": 1.0, "TBX5": 1.0, "NKX2-5": 1.0}
    
    result = service.predict_perturbation_trajectory("fibroblast", factors)
    
    assert "predicted_age_delta_years" in result
    assert result["predicted_age_delta_years"] < -5.0  # Significant rejuvenation shift
    assert "transcriptomic_stability" in result
    assert result["transcriptomic_stability"] > 0.90   # High stability
    assert "expression_profiles" in result
    assert "TNNT2" in result["expression_profiles"]
    assert result["expression_profiles"]["TNNT2"] > 2.50
    assert result["chromatin_state"] == "OPEN_ACCESSIBLE"
    assert result["status"] == "CONVERGED"

def test_multiomics_oncogenic_myc():
    service = MultiOmicsPredictorService()
    # Adding oncogenic MYC should trigger instability and decrease safety delta
    factors = {"GATA4": 1.0, "MEF2C": 1.0, "TBX5": 1.0, "MYC": 2.5}
    
    result = service.predict_perturbation_trajectory("fibroblast", factors)
    
    assert result["transcriptomic_stability"] < 0.90   # Compromised stability due to high MYC
    assert result["status"] == "METASTABLE_DRIFT"
    assert result["predicted_age_delta_years"] > -5.0  # Rejuvenation is reduced or reversed due to oncogenic drift

def test_multiomics_immune_cell():
    service = MultiOmicsPredictorService()
    factors = {"GATA4": 1.0, "MEF2C": 1.0, "TBX5": 1.0}
    
    # Immune cell macrophages resist transdifferentiation, yielding lower expression levels
    result_fibro = service.predict_perturbation_trajectory("fibroblast", factors)
    result_macro = service.predict_perturbation_trajectory("macrophage", factors)
    
    assert result_macro["expression_profiles"]["TNNT2"] < result_fibro["expression_profiles"]["TNNT2"]

if __name__ == "__main__":
    print("Running Multi-Omics Predictor unit tests...")
    test_multiomics_cardiac_cocktail()
    test_multiomics_oncogenic_myc()
    test_multiomics_immune_cell()
    print("All tests passed!")
