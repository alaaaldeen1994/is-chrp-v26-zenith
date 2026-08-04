"""
Phase 4 Discovery Engine & Virtual Trial Test Suite
===================================================
Validates:
  1. AlphaZen RL Reprogramming Cocktail Engine
  2. Virtual Adaptive Clinical Trial Engine
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.alphazen_rl_engine import run_alphazen_optimization
from services.virtual_trial_engine import run_virtual_adaptive_trial


class TestPhase4Services(unittest.TestCase):

    def test_alphazen_rl_engine(self):
        res = run_alphazen_optimization(initial_cell_age_years=65.0, n_rollout_episodes=50)

        self.assertIn("optimal_discovered_cocktail", res)
        self.assertGreater(len(res["optimal_discovered_cocktail"]["factors_and_dosages"]), 0)
        self.assertLess(res["optimal_discovered_cocktail"]["final_predicted_age_years"], 65.0)
        self.assertEqual(len(res["top_5_discovered_cocktails"]), 5)
        print("AlphaZen RL Engine Test: PASSED")

    def test_virtual_trial_engine(self):
        res = run_virtual_adaptive_trial(n_patients=200, dose_arms_mg=[10.0, 50.0])

        self.assertIn("optimal_dose_recommendation", res)
        self.assertEqual(len(res["dose_arms_evaluated"]), 2)
        self.assertGreater(res["optimal_dose_recommendation"]["overall_responder_rate_percent"], 0.0)
        self.assertIn("NNT", res["optimal_dose_recommendation"])
        print("Virtual Adaptive Trial Engine Test: PASSED")


if __name__ == "__main__":
    unittest.main()
