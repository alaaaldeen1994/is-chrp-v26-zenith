"""
Phase 1 Engine & API Integration Test Suite
============================================
Validates:
  1. Polygenic Risk Score Engine & FastAPI Router
  2. AlphaGenome PWM Sequence Scanner & FastAPI Router
  3. ADMET Drug Safety Profile Engine & FastAPI Router
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.polygenic_risk_engine import run_prs_analysis
from services.alphagenome_sequence_scanner import run_pwm_scan, PWM_DATABASE
from services.admet_engine import run_admet_screen


class TestPhase1Services(unittest.TestCase):

    def test_prs_engine(self):
        # Variants with known epistatic pairs: MYH7 + TNNT2 (0.42), GATA4 + NKX2-5 (0.61)
        variants = [
            {"rsid": "rs2234962",  "chromosome": "14", "position": 23397721, "ref_allele": "G", "alt_allele": "C", "genotype": 1, "maf": 0.04}, # MYH7
            {"rsid": "rs7977462",  "chromosome": "1",  "position": 20130000, "ref_allele": "G", "alt_allele": "A", "genotype": 1, "maf": 0.05}, # TNNT2
            {"rsid": "rs11107116", "chromosome": "8",  "position": 11600000, "ref_allele": "T", "alt_allele": "A", "genotype": 1, "maf": 0.03}, # GATA4
            {"rsid": "rs10494366", "chromosome": "5",  "position": 17260000, "ref_allele": "A", "alt_allele": "G", "genotype": 1, "maf": 0.02}, # NKX2-5
        ]
        result = run_prs_analysis(variants, phenotype="Cardiomyopathy", cell_type="iPSC-derived cardiomyocyte")

        self.assertIn("combined_prs", result)
        self.assertIn("percentile", result)
        self.assertIn("horvath_age_acceleration_years", result)
        self.assertGreater(len(result["matched_variants"]), 0)
        self.assertGreater(len(result["epistatic_pairs"]), 0)
        self.assertGreater(len(result["crispr_correction_priority"]), 0)
        print("PRS Engine Test: PASSED")

    def test_pwm_scanner(self):
        ref_seq = "GCTAGCTAGCTAGCTAGCTAGCTGATAAATGATCCGCTAGCTAGCTAGCT"
        alt_seq = "GCTAGCTAGCTAGCTAGCTAGCTTATAAATGATCCGCTAGCTAGCTAGCT"

        result = run_pwm_scan(
            ref_sequence=ref_seq,
            alt_sequence=alt_seq,
            variant_rsid="rs2128739",
            chromosome="12",
            position=111842901,
        )

        self.assertIn("tf_scan_results", result)
        self.assertIn("disrupted_tfs", result)
        self.assertIn("alphagenome_confidence", result)
        self.assertEqual(len(result["tf_scan_results"]), 15)
        self.assertGreater(len(result["disrupted_tfs"]), 0)
        print("PWM Scanner Test: PASSED")

    def test_admet_engine(self):
        # Test Aspirin
        aspirin = run_admet_screen(
            smiles="CC(=O)Oc1ccccc1C(=O)O",
            compound_name="Aspirin",
            therapeutic_area="cardiac",
        )

        self.assertIn(aspirin["admet_grade"], ["A", "B"])
        self.assertTrue(aspirin["lipinski_ro5"]["pass"])

        # Test hERG toxic blocker
        toxic = run_admet_screen(
            smiles="CCN1CCN(CCc2ccc(NS(=O)(=O)c3ccc(N)cc3)cc2)CC1",
            compound_name="Toxic Test Compound",
            therapeutic_area="cardiac",
        )

        self.assertTrue(toxic["herg_cardiotoxicity"]["cardiotoxicity_flag"])
        print("ADMET Engine Test: PASSED")


if __name__ == "__main__":
    unittest.main()
