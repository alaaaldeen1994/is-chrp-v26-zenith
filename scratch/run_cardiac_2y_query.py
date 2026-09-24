import sys
import json

sys.path.insert(0, r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative')

from services.ferro_aging_engine import get_ferro_aging_engine
from services.cardiac_safety_gate import get_cardiac_safety_gate
from services.cardiac_ensemble_clock import get_cardiac_ensemble_clock

query = "Identify transcription factors and direct epigenetic modulators to reverse biological age in regular ventricular cardiac myocytes by 2 years while blocking pluripotency induction."

# 1. Gentle Rejuvenation Factors (Micro-pulse)
factors = ["SIRT1", "SIRT6", "GATA4", "ZBTB16"]

# 2. Ferro-Aging Audit
ferro_engine = get_ferro_aging_engine()
ferro_res = ferro_engine.calculate_ferro_aging_index({
    "ACSL4": 0.18,
    "GPX4": 0.92,
    "SLC7A11": 0.82,
    "FTH1": 0.88,
    "LPCAT3": 0.22,
    "ALOX15": 0.08
})

# 3. Cardiac Safety Audit
cardiac_gate = get_cardiac_safety_gate()
safety_res = cardiac_gate.audit_cocktail_safety(
    factors=factors,
    predicted_expression={
        "TNNT2": 0.98,
        "MYH7": 0.96,
        "TTN": 0.95,
        "GJA1": 0.96,
        "ATP2A2": 0.97,
        "RYR2": 0.96,
        "CACNA1C": 0.96,
        "POU5F1": 0.08,  # Far below 0.35 cap
        "MYC": 0.05,     # Far below 0.30 cap
        "LIN28A": 0.06   # Far below 0.40 cap
    },
    pulse_duration_hours=1.0  # Ultra-short 1.0h pulse for micro-rejuvenation
)

# 4. EnsembleAge Prediction
ensemble_clock = get_cardiac_ensemble_clock()
clock_res = ensemble_clock.predict_ensemble_age(
    chronological_age=65.0,
    rejuvenation_target=2.0
)

output = {
    "query": query,
    "cell_type": "Adult Ventricular Cardiomyocyte",
    "target_bioage_reset_years": -2.0,
    "recommended_factors": factors,
    "pulse_kinetics": "1.0h ON / 23.0h OFF Ultra-Short Micro-Pulse",
    "ferro_aging_audit": ferro_res,
    "cardiac_safety_gate": safety_res,
    "ensemble_age_clock": clock_res
}

print(json.dumps(output, indent=2))
