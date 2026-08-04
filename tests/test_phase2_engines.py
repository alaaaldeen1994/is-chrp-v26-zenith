"""
Phase 2 Causal Engine & API Integration Test Suite
===================================================
Validates:
  1. Mendelian Randomisation Causal Inference Engine
  2. MOFA+ Multi-Omics Integration Engine
  3. Epistatic GRN Causal Mapper Engine
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.mendelian_randomisation_engine import run_mendelian_randomisation
from services.multiomics_integration_engine import run_mofa_integration
from services.epistatic_grn_mapper import run_causal_grn_map, predict_downstream_cascade, find_minimal_intervention_set


class TestPhase2Services(unittest.TestCase):

    def test_mendelian_randomisation(self):
        res = run_mendelian_randomisation("GATA4_expression", "Epigenetic_Age_Acceleration")

        self.assertIn("ivw_mr_results", res)
        self.assertIn("mr_egger_pleiotropy_test", res)
        self.assertIn("directionality_steiger_test", res)
        self.assertTrue(res["ivw_mr_results"]["statistically_significant"])
        self.assertTrue(res["instrument_strength"]["strong_instrument_pass"])
        print("Mendelian Randomisation Engine Test: PASSED")

    def test_mofa_multiomics_integration(self):
        res = run_mofa_integration("PATIENT_TEST_001", n_factors=10)

        self.assertEqual(len(res["latent_factor_loadings"]), 10)
        self.assertIn("horvath_epigenetic_age_delta_years", res)
        self.assertGreater(len(res["multiomic_therapeutic_targets"]), 0)
        print("MOFA+ Multi-Omics Engine Test: PASSED")

    def test_epistatic_grn_causal_mapper(self):
        # 1. Cascade test
        cascade_res = predict_downstream_cascade("GATA4", action="OVEREXPRESS", max_depth=2)
        self.assertGreater(cascade_res["affected_genes_count"], 0)

        # 2. MIS test
        desired = {"CDKN2A": "DOWN", "MYH7": "UP"}
        mis_res = find_minimal_intervention_set(desired)
        self.assertGreater(len(mis_res["minimal_intervention_sets"]), 0)

        # 3. Combined map
        full_res = run_causal_grn_map("TP53", "KNOCKOUT", desired_state=desired)
        self.assertGreater(full_res["total_causal_tfs"], 0)
        print("Epistatic GRN Causal Mapper Test: PASSED")


if __name__ == "__main__":
    unittest.main()
