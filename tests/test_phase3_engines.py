"""
Phase 3 Molecular Intervention Engine Test Suite
=================================================
Validates:
  1. Structural Protein-Drug Docking Engine
  2. Prime Editor Design Engine
  3. LNP Delivery Optimizer v2 (SORT technology)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.docking_engine import run_docking_simulation
from services.prime_editor_engine import run_prime_editor_design
from services.lnp_optimizer_v2 import run_lnp_optimization_v2


class TestPhase3Services(unittest.TestCase):

    def test_docking_engine(self):
        res = run_docking_simulation("GATA4", "P43694", "CC(=O)Oc1ccccc1C(=O)O", "Aspirin")

        self.assertIn("binding_affinity", res)
        self.assertIn("off_target_selectivity_screen", res)
        self.assertLess(res["binding_affinity"]["dG_bind_kcal_mol"], 0.0)
        self.assertGreater(len(res["off_target_selectivity_screen"]["off_target_panel_results"]), 0)
        print("Docking Engine Test: PASSED")

    def test_prime_editor_engine(self):
        context = "GCTAGCTAGCTAGCTAGCTAGCTAGGATCCGCTAGCTAGCTAGCTAGCTAGGATCCGCTAGCTAGCTAGCTAGCTAGGATCCGCTAGCTAGCTAGCTAG"
        res = run_prime_editor_design("MYH7", context, 50, "C>T", "PE3")

        self.assertIn("pegRNA_construct", res)
        self.assertIn("deepprime_predicted_efficiency_percent", res["efficiency_and_folding"])
        self.assertIsNotNone(res["nicking_sgRNA"])
        self.assertGreater(res["efficiency_and_folding"]["deepprime_predicted_efficiency_percent"], 50.0)
        print("Prime Editor Engine Test: PASSED")

    def test_lnp_optimizer_v2(self):
        res = run_lnp_optimization_v2("heart", "Prime Editor pegRNA", 4.5)

        self.assertIn("sort_formulation", res)
        self.assertEqual(res["delivery_job"]["target_organ"], "Heart")
        self.assertGreater(res["delivery_performance"]["predicted_organ_tropism_selectivity_percent"], 70.0)
        self.assertIn("DOTAP", res["sort_formulation"]["sort_5th_lipid"])
        print("LNP Optimizer v2 Test: PASSED")


if __name__ == "__main__":
    unittest.main()
