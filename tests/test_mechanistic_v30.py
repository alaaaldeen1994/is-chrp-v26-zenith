import sys
import os
import numpy as np

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.multiomics_service import MultiOmicsPredictorService
from services.pkpd_engine import PKPDEngine

def test_pkpd_dynamics():
    # Verify PK/PD engine executes and generates valid profiles
    time_pts, tissue_conc, avg_conc = PKPDEngine.simulate_dosing("Semaglutide", 1.0, 168.0, duration_days=14)
    
    assert len(time_pts) == 30
    assert len(tissue_conc) == 30
    assert avg_conc > 0.0
    
    # Test oral absorption deamidation penalty mapping
    _, _, nmn_conc_iv = PKPDEngine.simulate_dosing("NMN", 500.0, 24.0)
    # Intracellular concentration must be bounded and positive
    assert nmn_conc_iv > 0.0

def test_pathway_synergy():
    service = MultiOmicsPredictorService()
    
    # Baseline with no interventions
    factors_base = {}
    res_base = service.predict_perturbation_trajectory("fibroblast", factors_base)
    
    # NMN alone (scaled slider input = 5.0, i.e., 500mg)
    factors_nmn = {"NMN": 5.0}
    res_nmn = service.predict_perturbation_trajectory("fibroblast", factors_nmn)
    
    # Semaglutide alone (weekly subcutaneous 1.0mg)
    factors_sema = {"Semaglutide": 1.0}
    res_sema = service.predict_perturbation_trajectory("fibroblast", factors_sema)
    
    # Combination (NMN + Semaglutide)
    factors_combo = {"NMN": 5.0, "Semaglutide": 1.0}
    res_combo = service.predict_perturbation_trajectory("fibroblast", factors_combo)
    
    # Dosing combo should create a non-linear metabolic synergy in Sirtuin Activity
    # due to GLP1R-AMPK-NAMPT pathway salvage multiplication
    assert res_combo["sirtuin_activity_index"] > res_nmn["sirtuin_activity_index"]
    assert res_combo["sirtuin_activity_index"] > res_sema["sirtuin_activity_index"]

def test_cpg_methylation_vector():
    service = MultiOmicsPredictorService()
    factors = {"OCT4": 1.0, "SOX2": 1.0, "KLF4": 1.0}
    
    res = service.predict_perturbation_trajectory("fibroblast", factors)
    
    assert "timeseq_data" in res
    assert "cpg_methylation_vector" in res["timeseq_data"]
    
    cpg_vec = res["timeseq_data"]["cpg_methylation_vector"]
    assert len(cpg_vec) == 100
    
    # All CpG sites must remain mathematically bounded in [0.0, 1.0]
    for mk in cpg_vec:
        assert 0.0 <= mk <= 1.0

def test_damage_adaptation_decoupling():
    service = MultiOmicsPredictorService()
    
    # Baseline
    res_base = service.predict_perturbation_trajectory("fibroblast", {})
    
    # Chemotherapy intervention (Decitabine) increases DamAge significantly
    res_chemo = service.predict_perturbation_trajectory("fibroblast", {"Decitabine": 1.0})
    
    # Metabolic support (Omega3) decreases DamAge and increases AdaptAge
    res_support = service.predict_perturbation_trajectory("fibroblast", {"Omega3": 1.0})
    
    # Verify independent, decoupled behavior
    assert res_chemo["clinical_provenance"]["omega3_damage_clock_shift_years"] > 0.0
    assert res_support["clinical_provenance"]["omega3_damage_clock_shift_years"] < 0.0
    assert res_support["clinical_provenance"]["omega3_adaptive_clock_shift_years"] > 0.0

if __name__ == "__main__":
    print("Running Zenith v30 Mechanistic Rejuvenation Engine unit tests...")
    test_pkpd_dynamics()
    test_pathway_synergy()
    test_cpg_methylation_vector()
    test_damage_adaptation_decoupling()
    print("All mechanistic v30 tests passed successfully!")
