"""
test_partial_safety.py
~~~~~~~~~~~~~~~~~~~~~~
ZENITH PARTIAL REPROGRAMMING â€” INSTITUTIONAL TEST SUITE v2.0

A comprehensive, production-grade test suite for the Safety Firewall,
Sirtuin Pathway Scorer, Horvath Clock Enrichment, and database integrity.

Test Categories:
    1. Oncogene Firewall (hard safety boundary)
    2. TERT Special Case (mode-dependent gate)
    3. Dedifferentiation Risk Filter
    4. Safe Factor Scoring & Bio-Age Penalty
    5. Sirtuin/NAD+ Pathway Analysis
    6. Horvath Clock CpG Enrichment
    7. Safety Summary Aggregation
    8. Database Integrity Guards
    9. Edge Cases & Boundary Conditions
   10. Regression Tests (known past bugs)
   11. Cross-Mode Consistency Validation

References:
    - Sarkar et al. (2020) Nature Cell Biology â€” 13-year rejuvenation limit
    - Sinclair DA et al. (2020) Nature 588:124-129 â€” OSK vision restoration
    - Horvath S (2013) Genome Biology 14:R115 â€” Epigenetic clock

Author: Nilus Lab â€” Quality Assurance Division
Date: 2026-05-01
Classification: INSTITUTIONAL (RUO)
"""

import unittest
import sys
import time
from typing import List, Dict

from partial_safety import (
    filter_for_partial_reprogramming,
    score_sirtuin_pathway,
    score_horvath_impact,
    _score_factor,
    ONCOGENE_BLACKLIST,
    FULL_DEDIFF_RISK,
    PARTIAL_SAFE_FACTORS,
    HORVATH_CLOCK_GENES,
    CLOCK_GENE_REGULATORS,
    SIRTUIN_PATHWAY,
)


# ============================================================
# HELPERS
# ============================================================

def _approved_genes(result: Dict) -> List[str]:
    return [a["gene"] for a in result["approved"]]

def _blocked_genes(result: Dict) -> List[str]:
    return [b["gene"] for b in result["blocked"]]

def _blocked_categories(result: Dict) -> List[str]:
    return [b.get("category", "") for b in result["blocked"]]


# ============================================================
# 1. ONCOGENE FIREWALL
# ============================================================

class TestOncogeneFirewall(unittest.TestCase):
    """
    CRITICAL: Oncogenes must NEVER pass the filter in conservative or balanced mode.
    This is the single most important safety boundary in the platform.
    """

    def test_myc_blocked_all_modes(self):
        """c-MYC is a proto-oncogene â€” must be blocked in ALL modes including aggressive."""
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                result = filter_for_partial_reprogramming(["MYC"], mode=mode)
                self.assertIn("MYC", _blocked_genes(result),
                              f"CRITICAL: MYC leaked through in {mode} mode!")

    def test_kras_blocked_all_modes(self):
        """KRAS drives constitutive growth signaling â€” never safe."""
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                self.assertIn("KRAS", _blocked_genes(
                    filter_for_partial_reprogramming(["KRAS"], mode=mode)))

    def test_braf_blocked_all_modes(self):
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                self.assertIn("BRAF", _blocked_genes(
                    filter_for_partial_reprogramming(["BRAF"], mode=mode)))

    def test_bcl2_blocked_all_modes(self):
        """BCL2 blocks apoptosis â€” immortalization risk."""
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                self.assertIn("BCL2", _blocked_genes(
                    filter_for_partial_reprogramming(["BCL2"], mode=mode)))

    def test_all_oncogenes_blocked_balanced(self):
        """Submit the entire oncogene blacklist â€” every single entry must be blocked."""
        all_oncogenes = list(ONCOGENE_BLACKLIST.keys())
        result = filter_for_partial_reprogramming(all_oncogenes, mode="balanced")
        for gene in all_oncogenes:
            self.assertIn(gene, _blocked_genes(result),
                          f"CRITICAL: {gene} leaked through balanced mode!")

    def test_oncogene_blocked_category_is_correct(self):
        """Blocked oncogenes must be tagged with category 'oncogene_blacklist'."""
        result = filter_for_partial_reprogramming(["MYC", "KRAS"], mode="balanced")
        for b in result["blocked"]:
            self.assertEqual(b["category"], "oncogene_blacklist",
                             f"{b['gene']} should have category=oncogene_blacklist")

    def test_oncogene_has_reason_string(self):
        """Each blocked oncogene must include a human-readable reason."""
        result = filter_for_partial_reprogramming(["MYC"], mode="balanced")
        self.assertTrue(len(result["blocked"][0]["reason"]) > 10,
                        "Blocked reason should be a descriptive string")


# ============================================================
# 2. TERT SPECIAL CASE
# ============================================================

class TestTERTGate(unittest.TestCase):
    """
    TERT (telomerase) has a unique rule:
    - Blocked in conservative and balanced (immortalization risk)
    - Allowed in aggressive mode ONLY, with a low safety override (<=40)
    """

    def test_tert_blocked_conservative(self):
        self.assertIn("TERT", _blocked_genes(
            filter_for_partial_reprogramming(["TERT"], mode="conservative")))

    def test_tert_blocked_balanced(self):
        self.assertIn("TERT", _blocked_genes(
            filter_for_partial_reprogramming(["TERT"], mode="balanced")))

    def test_tert_allowed_aggressive(self):
        self.assertIn("TERT", _approved_genes(
            filter_for_partial_reprogramming(["TERT"], mode="aggressive")))

    def test_tert_aggressive_safety_capped(self):
        """When allowed in aggressive, safety_score must be <= 40 (high-risk flag)."""
        result = filter_for_partial_reprogramming(["TERT"], mode="aggressive")
        tert = next(a for a in result["approved"] if a["gene"] == "TERT")
        self.assertLessEqual(tert["safety_score"], 40)


# ============================================================
# 3. DEDIFFERENTIATION RISK FILTER
# ============================================================

class TestDedifferentiationFilter(unittest.TestCase):
    """
    Full-dedifferentiation factors (OCT4/POU5F1, NANOG, LIN28A) are blocked
    in conservative and balanced modes to prevent teratoma formation.
    """

    DEDIFF_FACTORS = ["POU5F1", "OCT4", "NANOG", "LIN28A"]

    def test_all_dediff_blocked_conservative(self):
        for gene in self.DEDIFF_FACTORS:
            with self.subTest(gene=gene):
                self.assertIn(gene, _blocked_genes(
                    filter_for_partial_reprogramming([gene], mode="conservative")))

    def test_all_dediff_blocked_balanced(self):
        for gene in self.DEDIFF_FACTORS:
            with self.subTest(gene=gene):
                self.assertIn(gene, _blocked_genes(
                    filter_for_partial_reprogramming([gene], mode="balanced")))

    def test_dediff_allowed_aggressive(self):
        """In aggressive mode, dediff factors should pass with low safety."""
        for gene in self.DEDIFF_FACTORS:
            with self.subTest(gene=gene):
                self.assertIn(gene, _approved_genes(
                    filter_for_partial_reprogramming([gene], mode="aggressive")))

    def test_dediff_aggressive_safety_is_low(self):
        result = filter_for_partial_reprogramming(["POU5F1"], mode="aggressive")
        pou5f1 = next(a for a in result["approved"] if a["gene"] == "POU5F1")
        self.assertLessEqual(pou5f1["safety_score"], 30)

    def test_dediff_category_is_correct(self):
        result = filter_for_partial_reprogramming(["NANOG"], mode="balanced")
        self.assertEqual(result["blocked"][0]["category"], "dedifferentiation_risk")


# ============================================================
# 4. SAFE FACTOR SCORING
# ============================================================

class TestSafeFactorScoring(unittest.TestCase):
    """Tests scoring logic for known-safe factors from the curated database."""

    def test_sirt1_scores(self):
        result = filter_for_partial_reprogramming(["SIRT1"], mode="balanced", bio_age=0.0)
        s = result["approved"][0]
        self.assertEqual(s["safety_score"], 98)
        self.assertEqual(s["longevity_score"], 99)
        self.assertTrue(s["sirtuin_pathway"])

    def test_foxo3_scores(self):
        result = filter_for_partial_reprogramming(["FOXO3"], mode="balanced", bio_age=0.0)
        f = result["approved"][0]
        self.assertEqual(f["safety_score"], 95)
        self.assertEqual(f["longevity_score"], 95)

    def test_gata4_not_sirtuin(self):
        result = filter_for_partial_reprogramming(["GATA4"], mode="balanced")
        self.assertFalse(result["approved"][0]["sirtuin_pathway"])

    def test_bio_age_penalty(self):
        """Higher bio_age should reduce safety score by up to 5 points."""
        young = filter_for_partial_reprogramming(["KLF4"], bio_age=0.0)
        old = filter_for_partial_reprogramming(["KLF4"], bio_age=1.0)
        self.assertGreater(young["approved"][0]["safety_score"],
                           old["approved"][0]["safety_score"])

    def test_bio_age_zero_no_penalty(self):
        result = filter_for_partial_reprogramming(["SIRT1"], bio_age=0.0)
        self.assertEqual(result["approved"][0]["safety_score"], 98)

    def test_bio_age_max_penalty(self):
        """At bio_age=1.0, penalty is int(1.0*5)=5 points."""
        result = filter_for_partial_reprogramming(["SIRT1"], bio_age=1.0)
        self.assertEqual(result["approved"][0]["safety_score"], 93)  # 98 - 5

    def test_unknown_factor_defaults(self):
        result = filter_for_partial_reprogramming(["UNKNOWN_GENE_XYZ"], mode="balanced")
        u = result["approved"][0]
        self.assertEqual(u["safety_score"], 60)
        self.assertEqual(u["longevity_score"], 50)
        self.assertFalse(u["sirtuin_pathway"])
        self.assertIn("not in curated database", u["notes"])

    def test_all_safe_factors_have_notes(self):
        """Every entry in PARTIAL_SAFE_FACTORS must have a 'notes' field."""
        for gene, data in PARTIAL_SAFE_FACTORS.items():
            with self.subTest(gene=gene):
                self.assertIn("notes", data, f"{gene} missing 'notes' field")
                self.assertTrue(len(data["notes"]) > 5)


# ============================================================
# 5. SIRTUIN PATHWAY SCORER
# ============================================================

class TestSirtuinPathway(unittest.TestCase):
    """Tests the Sirtuin/NAD+ longevity axis scoring."""

    def test_pure_sirtuin_100_percent(self):
        report = score_sirtuin_pathway(["SIRT1", "FOXO3", "NAMPT"])
        self.assertEqual(report["pathway_score"], 100)
        self.assertEqual(report["sinclair_relevance"], "HIGH")

    def test_mixed_50_percent(self):
        report = score_sirtuin_pathway(["SIRT1", "FOXO3", "GATA4", "TBX5"])
        self.assertEqual(report["pathway_score"], 50)

    def test_zero_percent_no_sirtuin(self):
        report = score_sirtuin_pathway(["GATA4", "TBX5", "NKX2-5"])
        self.assertEqual(report["pathway_score"], 0)
        self.assertEqual(report["sinclair_relevance"], "LOW")

    def test_nad_boost_with_nampt(self):
        self.assertTrue(score_sirtuin_pathway(["NAMPT"])["nad_boost"])

    def test_no_nad_boost_without_biosynthesis(self):
        self.assertFalse(score_sirtuin_pathway(["SIRT1", "FOXO3"])["nad_boost"])

    def test_cr_mimicry_two_genes(self):
        self.assertTrue(
            score_sirtuin_pathway(["SIRT1", "FOXO3"])["caloric_restriction_mimicry"])

    def test_cr_mimicry_single_gene_fails(self):
        self.assertFalse(
            score_sirtuin_pathway(["SIRT1"])["caloric_restriction_mimicry"])

    def test_empty_input(self):
        report = score_sirtuin_pathway([])
        self.assertEqual(report["pathway_score"], 0)
        self.assertEqual(report["sinclair_relevance"], "LOW")
        self.assertFalse(report["nad_boost"])

    def test_sinclair_high_with_sirt1_foxo3(self):
        """SIRT1+FOXO3 should always trigger HIGH sinclair relevance."""
        report = score_sirtuin_pathway(["SIRT1", "FOXO3"])
        self.assertEqual(report["sinclair_relevance"], "HIGH")

    def test_on_off_pathway_separation(self):
        report = score_sirtuin_pathway(["SIRT1", "GATA4"])
        self.assertIn("SIRT1", report["on_pathway"])
        self.assertIn("GATA4", report["off_pathway"])


# ============================================================
# 6. HORVATH CLOCK SCORER
# ============================================================

class TestHorvathClock(unittest.TestCase):
    """Tests Horvath Clock CpG-associated gene enrichment."""

    def test_foxo3_sirt1_multiple_hits(self):
        report = score_horvath_impact(["FOXO3", "SIRT1"])
        self.assertGreaterEqual(report["loci_affected"], 3)

    def test_gata4_tbx5_hits_fhl2(self):
        report = score_horvath_impact(["GATA4", "TBX5"])
        self.assertIn("FHL2", report["genes_hit"])

    def test_neuronal_factors_zero_hits(self):
        report = score_horvath_impact(["ASCL1", "NEUROD2"])
        self.assertEqual(report["loci_affected"], 0)

    def test_total_loci_always_eight(self):
        self.assertEqual(score_horvath_impact([])["total_loci"], 8)

    def test_time_seq_always_true(self):
        self.assertTrue(score_horvath_impact(["SIRT1"])["time_seq_compatible"])

    def test_shift_thresholds(self):
        """Verify shift labels: strong(>=6), moderate(>=4), weak(>=2), minimal(<2)."""
        # Build a maximal factor set to hit many loci
        all_regulators = set()
        for regs in CLOCK_GENE_REGULATORS.values():
            all_regulators.update(regs)
        report = score_horvath_impact(list(all_regulators))
        # With all regulators, should hit most loci
        self.assertGreaterEqual(report["loci_affected"], 6)
        self.assertEqual(report["predicted_shift"], "strong")

    def test_regulators_matched_structure(self):
        report = score_horvath_impact(["SIRT1"])
        # regulators_matched should be a dict mapping clock_gene -> [matched_factors]
        self.assertIsInstance(report["regulators_matched"], dict)
        for gene, regs in report["regulators_matched"].items():
            self.assertIn("SIRT1", regs)


# ============================================================
# 7. SAFETY SUMMARY
# ============================================================

class TestSafetySummary(unittest.TestCase):
    """Tests the aggregated safety summary output."""

    def test_clean_cocktail_clear(self):
        r = filter_for_partial_reprogramming(["SIRT1", "FOXO3", "KLF4"], mode="balanced")
        self.assertTrue(r["safety_summary"]["oncogene_clear"])
        self.assertFalse(r["safety_summary"]["dedifferentiation_blocked"])

    def test_oncogene_not_clear(self):
        r = filter_for_partial_reprogramming(["SIRT1", "MYC"], mode="balanced")
        self.assertFalse(r["safety_summary"]["oncogene_clear"])

    def test_dediff_blocked_flag(self):
        r = filter_for_partial_reprogramming(["SIRT1", "NANOG"], mode="balanced")
        self.assertTrue(r["safety_summary"]["dedifferentiation_blocked"])

    def test_ceiling_enforced_balanced(self):
        r = filter_for_partial_reprogramming(["SIRT1"], mode="balanced")
        self.assertEqual(r["safety_summary"]["partial_ceiling"], "enforced")

    def test_ceiling_relaxed_aggressive(self):
        r = filter_for_partial_reprogramming(["SIRT1"], mode="aggressive")
        self.assertEqual(r["safety_summary"]["partial_ceiling"], "relaxed")

    def test_counts_correct(self):
        r = filter_for_partial_reprogramming(
            ["SIRT1", "FOXO3", "MYC", "NANOG"], mode="balanced")
        self.assertEqual(r["safety_summary"]["total_approved"], 2)
        self.assertEqual(r["safety_summary"]["total_blocked"], 2)

    def test_mode_echoed(self):
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                r = filter_for_partial_reprogramming(["SIRT1"], mode=mode)
                self.assertEqual(r["mode"], mode)

    def test_bio_age_echoed(self):
        r = filter_for_partial_reprogramming(["SIRT1"], bio_age=0.73)
        self.assertEqual(r["bio_age_input"], 0.73)


# ============================================================
# 8. DATABASE INTEGRITY
# ============================================================

class TestDatabaseIntegrity(unittest.TestCase):
    """Guards against accidental modification of the safety databases."""

    def test_oncogene_minimum_entries(self):
        self.assertGreaterEqual(len(ONCOGENE_BLACKLIST), 10)

    def test_critical_oncogenes_present(self):
        for g in ["MYC", "MYCN", "KRAS", "BRAF", "BCL2", "MDM2", "CDK4"]:
            self.assertIn(g, ONCOGENE_BLACKLIST, f"{g} missing from oncogene blacklist!")

    def test_dediff_includes_oct4_and_alias(self):
        self.assertIn("POU5F1", FULL_DEDIFF_RISK)
        self.assertIn("OCT4", FULL_DEDIFF_RISK)

    def test_safe_factors_minimum(self):
        self.assertGreaterEqual(len(PARTIAL_SAFE_FACTORS), 20)

    def test_horvath_exactly_eight(self):
        self.assertEqual(len(HORVATH_CLOCK_GENES), 8)

    def test_elovl2_is_first(self):
        self.assertEqual(HORVATH_CLOCK_GENES[0], "ELOVL2")

    def test_sirtuin_pathway_has_all_sections(self):
        for key in ["upstream_activators", "core_sirtuins", "nad_biosynthesis",
                     "downstream_targets"]:
            self.assertIn(key, SIRTUIN_PATHWAY, f"Missing pathway section: {key}")

    def test_all_seven_sirtuins_in_core(self):
        for i in range(1, 8):
            self.assertIn(f"SIRT{i}", SIRTUIN_PATHWAY["core_sirtuins"])

    def test_clock_regulators_reference_real_genes(self):
        """Every clock gene in the regulators dict must exist in the HORVATH list."""
        for gene in CLOCK_GENE_REGULATORS:
            self.assertIn(gene, HORVATH_CLOCK_GENES,
                          f"Regulator entry '{gene}' not in HORVATH_CLOCK_GENES")


# ============================================================
# 9. EDGE CASES & BOUNDARY CONDITIONS
# ============================================================

class TestEdgeCases(unittest.TestCase):
    """Tests unusual inputs that could cause crashes or unexpected behavior."""

    def test_empty_candidates(self):
        r = filter_for_partial_reprogramming([], mode="balanced")
        self.assertEqual(len(r["approved"]), 0)
        self.assertEqual(len(r["blocked"]), 0)

    def test_single_factor(self):
        r = filter_for_partial_reprogramming(["SIRT1"], mode="balanced")
        self.assertEqual(len(r["approved"]), 1)

    def test_duplicate_factors(self):
        """Submitting the same factor twice should process it twice."""
        r = filter_for_partial_reprogramming(["SIRT1", "SIRT1"], mode="balanced")
        self.assertEqual(len(r["approved"]), 2)

    def test_lowercase_input(self):
        """The filter normalizes to uppercase â€” lowercase should still work."""
        r = filter_for_partial_reprogramming(["sirt1"], mode="balanced")
        self.assertEqual(r["approved"][0]["gene"], "SIRT1")

    def test_whitespace_in_gene_name(self):
        """Leading/trailing whitespace should be stripped."""
        r = filter_for_partial_reprogramming(["  SIRT1  "], mode="balanced")
        self.assertEqual(r["approved"][0]["gene"], "SIRT1")

    def test_large_cocktail(self):
        """20 factors at once â€” system should not crash."""
        factors = list(PARTIAL_SAFE_FACTORS.keys())[:20]
        r = filter_for_partial_reprogramming(factors, mode="balanced")
        self.assertGreater(len(r["approved"]), 0)

    def test_bio_age_zero(self):
        r = filter_for_partial_reprogramming(["SIRT1"], bio_age=0.0)
        self.assertEqual(r["approved"][0]["safety_score"], 98)

    def test_bio_age_one(self):
        r = filter_for_partial_reprogramming(["SIRT1"], bio_age=1.0)
        self.assertEqual(r["approved"][0]["safety_score"], 93)

    def test_mixed_safe_and_unsafe(self):
        """A cocktail with both safe and unsafe factors should split correctly."""
        r = filter_for_partial_reprogramming(
            ["SIRT1", "FOXO3", "MYC", "KRAS", "NANOG"], mode="balanced")
        self.assertEqual(len(r["approved"]), 2)  # SIRT1, FOXO3
        self.assertEqual(len(r["blocked"]), 3)   # MYC, KRAS, NANOG


# ============================================================
# 10. REGRESSION TESTS
# ============================================================

class TestRegressions(unittest.TestCase):
    """Tests for known past issues to prevent re-introduction."""

    def test_sirtuin_score_not_over_100(self):
        """Sirtuin pathway_score must never exceed 100%."""
        factors = ["SIRT1", "SIRT2", "SIRT3", "SIRT5", "SIRT6", "SIRT7",
                    "FOXO3", "FOXO1", "NAMPT", "NMNAT1", "PPARGC1A"]
        report = score_sirtuin_pathway(factors)
        self.assertLessEqual(report["pathway_score"], 100)

    def test_safety_score_never_negative(self):
        """Even at maximum bio_age, safety should not go below 0."""
        factor = _score_factor("ASCL1", bio_age=1.0)
        self.assertGreaterEqual(factor["safety_score"], 0)

    def test_horvath_loci_never_exceed_total(self):
        all_regs = set()
        for regs in CLOCK_GENE_REGULATORS.values():
            all_regs.update(regs)
        report = score_horvath_impact(list(all_regs))
        self.assertLessEqual(report["loci_affected"], report["total_loci"])

    def test_approved_blocked_no_overlap(self):
        """A gene must NEVER appear in both approved AND blocked."""
        r = filter_for_partial_reprogramming(
            ["SIRT1", "MYC", "FOXO3", "NANOG", "KLF4"], mode="balanced")
        approved = set(_approved_genes(r))
        blocked = set(_blocked_genes(r))
        self.assertEqual(len(approved & blocked), 0,
                         f"CRITICAL: Overlap detected: {approved & blocked}")


# ============================================================
# 11. CROSS-MODE CONSISTENCY
# ============================================================

class TestCrossModeConsistency(unittest.TestCase):
    """
    Validates that mode transitions follow the expected hierarchy:
    conservative (strictest) -> balanced -> aggressive (most permissive)
    """

    def test_conservative_blocks_more_than_aggressive(self):
        """Conservative mode must block >= the number blocked in aggressive."""
        factors = ["SIRT1", "FOXO3", "KLF4", "MYC", "POU5F1", "TERT", "NANOG"]
        r_con = filter_for_partial_reprogramming(factors, mode="conservative")
        r_agg = filter_for_partial_reprogramming(factors, mode="aggressive")
        self.assertGreaterEqual(
            r_con["safety_summary"]["total_blocked"],
            r_agg["safety_summary"]["total_blocked"],
            "Conservative must block >= aggressive")

    def test_aggressive_approves_more_than_conservative(self):
        factors = ["SIRT1", "FOXO3", "KLF4", "MYC", "POU5F1", "TERT", "NANOG"]
        r_con = filter_for_partial_reprogramming(factors, mode="conservative")
        r_agg = filter_for_partial_reprogramming(factors, mode="aggressive")
        self.assertGreaterEqual(
            r_agg["safety_summary"]["total_approved"],
            r_con["safety_summary"]["total_approved"],
            "Aggressive must approve >= conservative")

    def test_safe_factors_same_across_modes(self):
        """Purely safe factors (SIRT1, FOXO3) should be approved in ALL modes."""
        for mode in ["conservative", "balanced", "aggressive"]:
            with self.subTest(mode=mode):
                r = filter_for_partial_reprogramming(["SIRT1", "FOXO3"], mode=mode)
                self.assertEqual(len(r["approved"]), 2)
                self.assertEqual(len(r["blocked"]), 0)


# ============================================================
# RUNNER
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  ZENITH SAFETY FIREWALL â€” INSTITUTIONAL TEST SUITE v2.0")
    print("  Nilus Lab | Quality Assurance Division")
    print("=" * 70)
    start = time.time()
    result = unittest.main(verbosity=2, exit=False)
    elapsed = time.time() - start
    print(f"\n{'=' * 70}")
    print(f"  COMPLETED IN {elapsed:.2f}s")
    print(f"{'=' * 70}")
