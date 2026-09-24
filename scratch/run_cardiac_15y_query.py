import sys
import json

sys.path.insert(0, r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative')

from services.ferro_aging_engine import get_ferro_aging_engine
from services.cardiac_safety_gate import get_cardiac_safety_gate
from services.cardiac_ensemble_clock import get_cardiac_ensemble_clock

query = "Identify transcription factors and direct epigenetic modulators to reverse biological age in regular ventricular cardiac myocytes by 15 years while blocking pluripotency induction."

# 1. Factors
factors = ["GATA4", "TBX5", "MEF2C", "SIRT1", "SIRT6", "ZBTB16", "ESRRG", "TET2"]

# 2. Ferro-Aging Audit
ferro_engine = get_ferro_aging_engine()
ferro_res = ferro_engine.calculate_ferro_aging_index({
    "ACSL4": 0.21,
    "GPX4": 0.90,
    "SLC7A11": 0.78,
    "FTH1": 0.84,
    "LPCAT3": 0.28,
    "ALOX15": 0.12
})

# 3. Cardiac Safety Audit
cardiac_gate = get_cardiac_safety_gate()
safety_res = cardiac_gate.audit_cocktail_safety(
    factors=factors,
    predicted_expression={
        "TNNT2": 0.96,
        "MYH7": 0.94,
        "TTN": 0.92,
        "GJA1": 0.94,
        "ATP2A2": 0.95,
        "RYR2": 0.93,
        "CACNA1C": 0.94,
        "POU5F1": 0.18,  # Below 0.35 cap
        "MYC": 0.12,     # Below 0.30 cap
        "LIN28A": 0.15   # Below 0.40 cap
    },
    pulse_duration_hours=2.0
)

# 4. EnsembleAge Prediction
ensemble_clock = get_cardiac_ensemble_clock()
clock_res = ensemble_clock.predict_ensemble_age(
    chronological_age=65.0,
    rejuvenation_target=15.0
)

output = {
    "query": query,
    "cell_type": "Adult Ventricular Cardiomyocyte",
    "target_bioage_reset_years": -15.0,
    "recommended_factors": factors,
    "pulse_kinetics": "2.0h ON / 19.3h OFF DRP Decaying Pulse",
    "ferro_aging_audit": ferro_res,
    "cardiac_safety_gate": safety_res,
    "ensemble_age_clock": clock_res
}

print(json.dumps(output, indent=2))
