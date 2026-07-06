import sys
import os

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.lnp_optimizer import LNPOptimizerService

def test_lnp_optimized_formulation():
    service = LNPOptimizerService()
    # Active targeting facilitates receptor-mediated transcytosis across myocardial continuous endothelium
    molar_ratios = {
        "ionizable": 50.0, "cholesterol": 38.5, "helper": 10.0, "peg": 1.5,
        "active_targeting": 1.0
    }
    np_ratio = 6.0
    
    result = service.evaluate_formulation(molar_ratios, np_ratio)
    
    assert "encapsulation_efficiency_percent" in result
    assert result["encapsulation_efficiency_percent"] > 90.0  # Efficient encapsulation
    assert "heart_selectivity_score" in result
    assert result["heart_selectivity_score"] > 0.50          # Good tropism selectivity
    assert result["formulation_status"] == "OPTIMIZED_DELIVERY"
    assert "zeta_potential_mv" in result["biophysical_metrics"]

def test_lnp_suboptimal_formulation():
    service = LNPOptimizerService()
    # High PEG ratio reduces heart selectivity; low N/P ratio drops encapsulation efficiency
    molar_ratios = {"ionizable": 30.0, "cholesterol": 40.0, "helper": 20.0, "peg": 10.0}
    np_ratio = 1.5
    
    result = service.evaluate_formulation(molar_ratios, np_ratio)
    
    assert result["encapsulation_efficiency_percent"] < 80.0
    assert result["heart_selectivity_score"] < 0.50
    assert result["formulation_status"] in ["SUBOPTIMAL", "LIVER_TRAPPED"]

if __name__ == "__main__":
    print("Running LNP Optimizer unit tests...")
    test_lnp_optimized_formulation()
    test_lnp_suboptimal_formulation()
    print("All tests passed!")
