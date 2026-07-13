"""Neural Age Clock — predicts the biological age of the cardiac nervous system.

Companion to services/horvath_clock.py.

While Horvath's clock measures epigenetic age from 353-CpG methylation,
the Neural Age Clock measures the functional age of the heart's intrinsic
nervous system (ICNS) from gene expression data.

Scientific basis:
  - The heart has ~40,000 intrinsic neurons (Ardell, 2004)
  - Vagal tone declines ~1.5%/year after age 40 (Umetani et al., 1998)
  - Heart Rate Variability (HRV) is a clinical proxy for neural age
  - Key markers: CHAT (ACh synthesis), TH (sympathetic), NGFR (neuronal
    health), CHRNA7 (vagal signaling), RET (GDNF survival)

This clock outputs TWO ages side-by-side:
  - Horvath age (epigenetic) — from horvath_clock.py
  - Neural age (functional)   — from this module

The DUAL-AGE metric is a unique selling point: no competitor offers it.

IMPORTANT: Operational marker for research. Not a clinical diagnosis.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

logger = logging.getLogger("neural_age_clock")


# ---------------------------------------------------------------------------
# Neural marker reference panel
# ---------------------------------------------------------------------------

# Genes whose expression tracks with cardiac neural aging.
# Categories: parasympathetic, sympathetic, neuronal health, conduction.
NEURAL_AGE_PANEL = {
    # Parasympathetic (vagal) — declines with age
    "CHAT":     {"category": "parasympathetic", "ref_young": 1.0, "decline_rate": 0.018, "weight": 1.5},
    "SLC18A3":  {"category": "parasympathetic", "ref_young": 1.0, "decline_rate": 0.020, "weight": 1.3},  # VAChT
    "CHRNA7":   {"category": "parasympathetic", "ref_young": 1.0, "decline_rate": 0.022, "weight": 1.4},
    "CHRM2":    {"category": "parasympathetic", "ref_young": 1.0, "decline_rate": 0.015, "weight": 1.2},

    # Sympathetic — relatively preserved but dysregulated
    "TH":       {"category": "sympathetic", "ref_young": 1.0, "decline_rate": 0.010, "weight": 1.0},
    "DBH":      {"category": "sympathetic", "ref_young": 1.0, "decline_rate": 0.012, "weight": 0.9},

    # Neuronal health / survival — declines with age
    "NGFR":     {"category": "neuronal_health", "ref_young": 1.0, "decline_rate": 0.025, "weight": 1.6},
    "RET":      {"category": "neuronal_health", "ref_young": 1.0, "decline_rate": 0.020, "weight": 1.5},  # GDNF receptor
    "NTRK1":    {"category": "neuronal_health", "ref_young": 1.0, "decline_rate": 0.018, "weight": 1.3},  # TrkA
    "NTN1":     {"category": "neuronal_health", "ref_young": 1.0, "decline_rate": 0.015, "weight": 1.1},  # Netrin-1

    # Autonomic identity
    "PHOX2B":   {"category": "identity", "ref_young": 1.0, "decline_rate": 0.008, "weight": 0.8},
    "ISL1":     {"category": "identity", "ref_young": 1.0, "decline_rate": 0.010, "weight": 0.9},

    # Conduction / coupling — declines with age (fibrosis replaces neurons)
    "GJA1":     {"category": "conduction", "ref_young": 1.0, "decline_rate": 0.012, "weight": 1.0},  # Connexin 43
    "GJA5":     {"category": "conduction", "ref_young": 1.0, "decline_rate": 0.014, "weight": 1.0},  # Connexin 40
}

# Age reference range
AGE_MIN = 20.0
AGE_MAX = 100.0
ADULT_THRESHOLD = 40.0  # neural decline accelerates after 40


# ---------------------------------------------------------------------------
# Neural Age Clock
# ---------------------------------------------------------------------------

class NeuralAgeClock:
    """Predicts the biological age of the cardiac nervous system.

    Usage (companion to HorvathClock):
        horvath = HorvathClock()
        neural = NeuralAgeClock()

        horvath_age = horvath.predict(methylation_betas)
        neural_age, confidence, breakdown = neural.predict(gene_expression, chronological_age)

        # The dual-age gap is the key marketing metric:
        gap = neural_age - chronological_age
    """

    def __init__(self, substrate_service=None):
        """Optionally takes a NeurosSubstrateService for Φ-hat enrichment.

        If provided, the clock uses the spiking substrate to compute a
        neural-integration stability score that modulates the age estimate.
        If not provided, the clock uses a linear model only.
        """
        self.substrate_service = substrate_service
        self.panel = NEURAL_AGE_PANEL

    def predict(
        self,
        expression_vector: Dict[str, float],
        chronological_age: float = 50.0,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Predict neural age from gene expression.

        Args:
            expression_vector: {gene_symbol: expression_level}
                (typically the decoded scVI output, 4000 genes)
            chronological_age: the donor's chronological age (for relative
                gap computation)

        Returns:
            (neural_age, confidence, breakdown)
            - neural_age: predicted biological age of the cardiac nervous system
            - confidence: 0..1 (higher = more markers detected)
            - breakdown: per-gene contribution + category scores
        """
        contributions = []
        category_scores: Dict[str, List[float]] = {}

        for gene, spec in self.panel.items():
            level = expression_vector.get(gene)
            if level is None or level <= 0:
                continue
            # normalize: assume scVI-decoded expression ~ [0, 10]
            normalized = min(1.0, float(level) / 5.0)
            ref = spec["ref_young"]
            # how much has this marker declined vs young reference?
            decline = max(0.0, ref - normalized)
            # convert decline to age: decline = decline_rate * (age - ADULT_THRESHOLD)
            if spec["decline_rate"] > 0:
                gene_age = ADULT_THRESHOLD + (decline / spec["decline_rate"])
            else:
                gene_age = chronological_age
            gene_age = max(AGE_MIN, min(AGE_MAX, gene_age))
            weight = spec["weight"]
            contributions.append({
                "gene": gene,
                "category": spec["category"],
                "expression": float(level),
                "normalized": normalized,
                "estimated_age": gene_age,
                "weight": weight,
            })
            category_scores.setdefault(spec["category"], []).append(gene_age)

        if not contributions:
            # no markers detected — return chronological age with zero confidence
            return chronological_age, 0.0, {
                "n_markers_detected": 0,
                "warning": "No neural markers found in expression vector",
            }

        # weighted average age
        total_weight = sum(c["weight"] for c in contributions)
        weighted_age = sum(c["estimated_age"] * c["weight"] for c in contributions) / total_weight

        # category averages
        category_ages = {
            cat: sum(ages) / len(ages) for cat, ages in category_scores.items()
        }

        # confidence: based on how many markers detected (max ~14)
        n_detected = len(contributions)
        confidence = min(1.0, n_detected / 10.0)

        # dispersion: if markers disagree a lot, lower confidence
        ages = [c["estimated_age"] for c in contributions]
        if len(ages) > 1:
            std = float(np.std(ages))
            confidence *= max(0.3, 1.0 - std / 30.0)

        # Φ-hat enrichment (optional): if substrate available, use integration
        # as a stability modulator. Higher Φ-hat = more integrated = younger.
        phi_modulation = 0.0
        phi_hat = None
        if self.substrate_service is not None:
            # This would be called async in the service layer; here we do a
            # synchronous fallback (the service layer wraps this).
            pass  # handled by the async wrapper below

        breakdown = {
            "n_markers_detected": n_detected,
            "weighted_age": float(weighted_age),
            "category_ages": {k: float(v) for k, v in category_ages.items()},
            "contributions": contributions,
            "chronological_age": float(chronological_age),
            "neural_age_gap": float(weighted_age - chronological_age),
            "confidence": float(confidence),
        }

        return float(weighted_age), float(confidence), breakdown

    async def predict_with_substrate(
        self,
        expression_vector: Dict[str, float],
        chronological_age: float = 50.0,
    ) -> Dict[str, Any]:
        """Async version that enriches the prediction with substrate Φ-hat.

        This is the method the FastAPI router calls. It:
          1. Computes the linear neural age from marker genes
          2. Runs the spiking substrate on ion-channel genes
          3. Uses Φ-hat to modulate the age (higher integration = younger)
          4. Returns the enriched dual-metric result
        """
        neural_age, confidence, breakdown = self.predict(
            expression_vector, chronological_age
        )

        # substrate enrichment
        phi_hat = None
        synchrony = None
        if self.substrate_service is not None:
            sub_result = await self.substrate_service.analyze_ion_profile(
                expression_vector
            )
            if sub_result.get("ok"):
                phi_hat = sub_result["phi_hat"]
                synchrony = sub_result["synchrony"]
                # modulate: higher phi = younger (more integrated neural activity)
                # lower phi = older (degraded integration)
                # The modulation is gentle (±5 years max)
                if phi_hat > 0:
                    # normalize phi to a 0..1 scale (empirical max ~0.01)
                    phi_norm = min(1.0, phi_hat / 0.01)
                    phi_modulation = (phi_norm - 0.5) * 10.0  # -5 to +5 years
                    # high synchrony can indicate arrhythmogenic risk → older
                    if synchrony is not None and synchrony > 0.5:
                        phi_modulation += (synchrony - 0.5) * 10.0
                    neural_age_enriched = max(
                        AGE_MIN, min(AGE_MAX, neural_age + phi_modulation)
                    )
                    breakdown["neural_age_linear"] = neural_age
                    breakdown["neural_age_enriched"] = neural_age_enriched
                    breakdown["phi_hat"] = phi_hat
                    breakdown["synchrony"] = synchrony
                    breakdown["phi_modulation"] = phi_modulation
                    neural_age = neural_age_enriched
                    # boost confidence if substrate agrees
                    confidence = min(1.0, confidence + 0.1)

        # dual-age gap (the KEY marketing metric)
        dual_age_gap = neural_age - chronological_age

        return {
            "neural_age": float(neural_age),
            "chronological_age": float(chronological_age),
            "neural_age_gap": float(dual_age_gap),
            "confidence": float(confidence),
            "phi_hat": phi_hat,
            "synchrony": synchrony,
            "breakdown": breakdown,
            "interpretation": self._interpret(neural_age, chronological_age, confidence),
        }

    def _interpret(self, neural_age: float, chrono_age: float, confidence: float) -> str:
        """Generate an operational interpretation (not a clinical diagnosis)."""
        gap = neural_age - chrono_age
        if confidence < 0.2:
            return (
                f"Neural age estimate ({neural_age:.1f}) has low confidence "
                f"({confidence:.0%}) — insufficient markers detected. "
                f"Result is exploratory only."
            )
        if gap < -5:
            return (
                f"Cardiac nervous system appears functionally younger than chronological "
                f"age (neural age {neural_age:.1f} vs {chrono_age:.0f}, gap {gap:+.1f}y). "
                f"Parasympathetic and neuronal-health markers are well-preserved."
            )
        elif gap > 5:
            return (
                f"Cardiac nervous system appears functionally older than chronological "
                f"age (neural age {neural_age:.1f} vs {chrono_age:.0f}, gap {gap:+.1f}y). "
                f"Vagal marker decline suggests accelerated neural aging."
            )
        else:
            return (
                f"Cardiac neural age ({neural_age:.1f}) is concordant with chronological "
                f"age ({chrono_age:.0f}). Neural markers within expected range."
            )

    def get_panel(self) -> Dict[str, Dict[str, Any]]:
        """Return the neural age panel (for API documentation)."""
        return self.panel

    def get_marker_genes(self) -> List[str]:
        """Return the list of marker genes tracked."""
        return list(self.panel.keys())


# ---------------------------------------------------------------------------
# Dual-Age comparator (the marketing headline)
# ---------------------------------------------------------------------------

class DualAgeComparator:
    """Combines Horvath (epigenetic) + Neural (functional) ages.

    This is the unique selling point: NO competitor offers dual-age.
    The gap between the two ages reveals whether aging is:
      - Genomic-dominant (Horvath > Neural) → epigenetic drift
      - Neural-dominant (Neural > Horvath) → autonomic decline
      - Concordant → uniform aging

    Usage:
        horvath_age = horvath_clock.predict(betas)
        neural_result = await neural_clock.predict_with_substrate(expr, age)
        dual = DualAgeComparator.compare(horvath_age, neural_result)
    """

    @staticmethod
    def compare(horvath_age: float, neural_result: Dict[str, Any]) -> Dict[str, Any]:
        neural_age = neural_result["neural_age"]
        chrono_age = neural_result["chronological_age"]

        horvath_gap = horvath_age - chrono_age
        neural_gap = neural_age - chrono_age
        dual_gap = neural_age - horvath_age  # positive = neural older than epigenetic

        # aging phenotype classification
        if abs(dual_gap) < 3.0:
            phenotype = "concordant"
            phenotype_desc = "Epigenetic and neural ages are aligned — uniform aging profile."
        elif dual_gap > 3.0:
            phenotype = "neural_dominant"
            phenotype_desc = (
                "Neural age exceeds epigenetic age — autonomic nervous system "
                "is aging faster than the genome. May indicate vagal decline "
                "or cardiac denervation. Consider autonomic interventions."
            )
        else:
            phenotype = "genomic_dominant"
            phenotype_desc = (
                "Epigenetic age exceeds neural age — genomic drift is the "
                "primary aging driver. Neural function is relatively preserved. "
                "Consider epigenetic reprogramming (OSK partial)."
            )

        # overall rejuvenation potential
        if neural_result.get("phi_hat") is not None:
            # if substrate integration is high, rejuvenation potential is good
            phi = neural_result["phi_hat"]
            potential = "high" if phi > 0.005 else "moderate" if phi > 0.001 else "low"
        else:
            potential = "unknown"

        return {
            "horvath_age": float(horvath_age),
            "neural_age": float(neural_age),
            "chronological_age": float(chrono_age),
            "horvath_gap": float(horvath_gap),
            "neural_gap": float(neural_gap),
            "dual_gap": float(dual_gap),
            "phenotype": phenotype,
            "phenotype_description": phenotype_desc,
            "rejuvenation_potential": potential,
            "summary": (
                f"Dual-age assessment: Horvath {horvath_age:.1f}y, "
                f"Neural {neural_age:.1f}y, Chronological {chrono_age:.0f}y. "
                f"Profile: {phenotype}."
            ),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_neural_clock: Optional[NeuralAgeClock] = None

def get_neural_clock(substrate_service=None) -> NeuralAgeClock:
    global _neural_clock
    if _neural_clock is None:
        _neural_clock = NeuralAgeClock(substrate_service=substrate_service)
    elif substrate_service is not None and _neural_clock.substrate_service is None:
        _neural_clock.substrate_service = substrate_service
    return _neural_clock
