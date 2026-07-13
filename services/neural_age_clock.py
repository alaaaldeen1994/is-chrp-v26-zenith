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

import json
import logging
import math
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

logger = logging.getLogger("neural_age_clock")

# Path to the real trained Ridge model from Colab training (v31 dual-model)
_MODEL_DIR = Path(__file__).parent.parent / "models" / "neural_age_clock_v1"
_CONFIG_PATH = _MODEL_DIR / "config.json"
_RIDGE_PATH  = _MODEL_DIR / "ridge_model.pkl"


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
# Ridge Neural Age Clock — real trained model from Colab (v31 dual-model)
# ---------------------------------------------------------------------------

class RidgeNeuralAgeClock:
    """Neural Age Clock backed by the real Ridge regression trained in Colab.

    Trained on 3,569 cells from TWO scVI models:
      - 486k cardiac specialist  (Litviňuková et al., Nature 2020)
      - 1.94M foundation model   (HCA Heart Atlas)

    Uses 8 real markers with Horvath-style log-transform:
      F0 = 40 (adult threshold)
      y_log = log(age+1)        if age <= 40
      y_log = (age-40)/20 + log(41)  if age > 40

    Falls back silently to the original NeuralAgeClock if model files
    are missing.
    """

    def __init__(self, substrate_service=None):
        self.substrate_service = substrate_service
        self._ridge   = None
        self._config  = None
        self._markers: List[str] = []
        self._weights: Dict[str, float] = {}
        self._intercept: float = 0.0
        self._fallback = NeuralAgeClock(substrate_service=substrate_service)
        self._load_model()

    def _load_model(self) -> None:
        """Load config.json from models/neural_age_clock_v1/."""
        try:
            if not _CONFIG_PATH.exists():
                logger.warning(
                    "[RidgeNeuralAgeClock] config.json not found at %s — "
                    "using fallback linear clock.", _MODEL_DIR
                )
                return

            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                self._config = json.load(f)

            self._markers   = self._config["markers"]
            self._weights   = self._config["weights"]
            self._intercept = self._config["intercept"]
            
            # Load scaling parameters (for standardized models)
            self._scaler_mean = self._config.get("scaler_mean")
            self._scaler_scale = self._config.get("scaler_scale")

            # Try loading ridge_model.pkl if present, but support manual fallback
            try:
                if _RIDGE_PATH.exists():
                    with open(_RIDGE_PATH, "rb") as f:
                        self._ridge = pickle.load(f)
            except Exception as pkl_exc:
                logger.warning("[RidgeNeuralAgeClock] Could not load pickle model (will use manual math fallback): %s", pkl_exc)
                self._ridge = None

            logger.info(
                "[RidgeNeuralAgeClock] Loaded v31 dual-model clock — "
                "%d markers, Pearson r=%.3f, MAE=%.1f yrs (training set)",
                len(self._markers),
                self._config["training"]["pearson_r"],
                self._config["training"]["mae_years"],
            )
        except Exception as exc:
            logger.error("[RidgeNeuralAgeClock] Failed to load model: %s", exc)
            self._ridge = None

    @property
    def is_loaded(self) -> bool:
        # Loaded if we have a config with weights
        return len(self._weights) > 0

    # Horvath-style inverse transform
    def _inverse_transform(self, y_log: float) -> float:
        F0 = float(self._config.get("adult_threshold", 40))
        log_F0p1 = math.log(F0 + 1)
        if y_log <= log_F0p1:
            return math.exp(y_log) - 1.0
        else:
            return (y_log - log_F0p1) * 20.0 + F0

    def predict(
        self,
        expression_vector: Dict[str, float],
        chronological_age: float = 50.0,
    ) -> Tuple[float, float, Dict[str, Any]]:
        """Predict neural age using real trained Ridge regression.

        Falls back to the original linear model if Ridge files are missing.
        """
        if not self.is_loaded:
            return self._fallback.predict(expression_vector, chronological_age)

        age_min = float(self._config.get("age_min", 20))
        age_max = float(self._config.get("age_max", 100))

        # Build feature vector in marker order
        x = np.array(
            [expression_vector.get(g, 0.0) for g in self._markers],
            dtype=np.float64
        ).reshape(1, -1)

        # Apply log1p transform (matching training script)
        x_log = np.log1p(x)

        # Predict using Ridge pipeline, with manual math fallback to bypass unpickling issues
        if self._ridge is not None:
            pred_val = float(self._ridge.predict(x_log)[0])
        else:
            # Manual StandardScaler + Ridge prediction math
            x_scaled = x_log.copy()
            if self._scaler_mean is not None and self._scaler_scale is not None:
                x_scaled = (x_log - np.array(self._scaler_mean)) / np.array(self._scaler_scale)
            
            # Predict: sum(x_scaled * weights) + intercept
            weights_arr = np.array([self._weights.get(g, 0.0) for g in self._markers])
            pred_val = float(np.sum(x_scaled * weights_arr) + self._intercept)
        
        # If it is the donor-level model, it predicts raw age directly (no log-transform on target)
        if "donor" in self._config.get("version", ""):
            neural_age = pred_val
        else:
            neural_age = self._inverse_transform(pred_val)
            
        neural_age = float(np.clip(neural_age, age_min, age_max))

        # Count detected markers (non-zero)
        detected = [g for g in self._markers if expression_vector.get(g, 0.0) > 0]
        n_detected = len(detected)
        confidence = min(1.0, n_detected / max(1, len(self._markers)))

        # Per-marker contributions for breakdown
        contributions = [
            {
                "gene": g,
                "expression": float(expression_vector.get(g, 0.0)),
                "weight": self._weights.get(g, 0.0),
                "category": NEURAL_AGE_PANEL.get(g, {}).get("category", "unknown"),
            }
            for g in self._markers
        ]

        breakdown = {
            "model": "RidgeNeuralAgeClock_v31_dual",
            "n_markers_detected": n_detected,
            "markers_used": self._markers,
            "contributions": contributions,
            "chronological_age": float(chronological_age),
            "neural_age_gap": float(neural_age - chronological_age),
            "confidence": float(confidence),
            "training_pearson_r": self._config["training"]["pearson_r"],
            "training_mae_years": self._config["training"]["mae_years"],
        }

        return neural_age, confidence, breakdown

    async def predict_with_substrate(
        self,
        expression_vector: Dict[str, float],
        chronological_age: float = 50.0,
    ) -> Dict[str, Any]:
        """Async version — delegates substrate enrichment then returns dual-age result."""
        neural_age, confidence, breakdown = self.predict(
            expression_vector, chronological_age
        )

        # Optional Φ-hat enrichment (same logic as NeuralAgeClock)
        phi_hat = None
        synchrony = None
        if self.substrate_service is not None:
            sub_result = await self.substrate_service.analyze_ion_profile(
                expression_vector
            )
            if sub_result.get("ok"):
                phi_hat  = sub_result["phi_hat"]
                synchrony = sub_result["synchrony"]
                if phi_hat and phi_hat > 0:
                    phi_norm = min(1.0, phi_hat / 0.01)
                    phi_modulation = (phi_norm - 0.5) * 10.0
                    if synchrony and synchrony > 0.5:
                        phi_modulation += (synchrony - 0.5) * 10.0
                    neural_age = float(
                        np.clip(neural_age + phi_modulation, AGE_MIN, AGE_MAX)
                    )
                    breakdown["phi_hat"] = phi_hat
                    breakdown["synchrony"] = synchrony
                    breakdown["phi_modulation"] = phi_modulation
                    confidence = min(1.0, confidence + 0.1)

        dual_age_gap = neural_age - chronological_age
        return {
            "neural_age":       float(neural_age),
            "chronological_age": float(chronological_age),
            "neural_age_gap":   float(dual_age_gap),
            "confidence":       float(confidence),
            "phi_hat":          phi_hat,
            "synchrony":        synchrony,
            "breakdown":        breakdown,
            "interpretation":   self._interpret(neural_age, chronological_age, confidence),
        }

    def _interpret(self, neural_age: float, chrono_age: float, confidence: float) -> str:
        """Reuse same interpretation as NeuralAgeClock."""
        return self._fallback._interpret(neural_age, chrono_age, confidence)

    def get_panel(self) -> Dict[str, Dict[str, Any]]:
        return NEURAL_AGE_PANEL

    def get_marker_genes(self) -> List[str]:
        return self._markers if self._markers else list(NEURAL_AGE_PANEL.keys())


# ---------------------------------------------------------------------------
# Singleton — prefers RidgeNeuralAgeClock (real trained) over linear fallback
# ---------------------------------------------------------------------------

_neural_clock: Optional[RidgeNeuralAgeClock] = None

def get_neural_clock(substrate_service=None) -> RidgeNeuralAgeClock:
    """Return the singleton RidgeNeuralAgeClock (real v31 dual-model trained weights)."""
    global _neural_clock
    if _neural_clock is None:
        _neural_clock = RidgeNeuralAgeClock(substrate_service=substrate_service)
        if _neural_clock.is_loaded:
            logger.info("[NeuralAgeClock] Using real trained RidgeNeuralAgeClock v31.")
        else:
            logger.warning("[NeuralAgeClock] Ridge model not found — using linear fallback.")
    elif substrate_service is not None and _neural_clock.substrate_service is None:
        _neural_clock.substrate_service = substrate_service
    return _neural_clock
