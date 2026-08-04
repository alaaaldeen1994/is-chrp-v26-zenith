"""
ADMET Drug Safety Profile Engine — Zenith Platform Phase 1
===========================================================
Computes pharmacokinetic and toxicity properties of drug candidates
from molecular SMILES strings using rule-based cheminformatics.

Implements:
  - Lipinski's Rule of Five (Ro5) — oral bioavailability
  - Veber rules — intestinal permeability
  - hERG cardiotoxicity structural alert detection
  - CYP3A4/2D6 inhibition substructure matching
  - Blood-brain barrier (BBB) permeability prediction
  - Hepatotoxicity structural alert scanning
  - PAINS/reactive group detection
  - Overall ADMET grade (A/B/C/D/F)

References:
  - Lipinski et al. (2001). Experimental and computational approaches
    to estimate solubility and permeability. Adv Drug Deliv Rev 46:3-26.
  - Veber et al. (2002). Molecular properties that influence oral
    bioavailability. J Med Chem 45(12):2615-2623.
  - Waring (2010). Defining optimum lipophilicity and molecular weight
    ranges for drug candidates. Bioorg Med Chem Lett 19:2844-2851.
  - Ertl et al. (2000). Fast calculation of molecular polar surface area.
    J Med Chem 43(20):3714-3717.
"""

import re
import math
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# FRAGMENT CONTRIBUTION TABLES (Crippen-Wildman method, simplified)
# Each fragment: (SMARTS-like pattern, logP contribution, MW contribution)
# ---------------------------------------------------------------------------

# Common functional group LogP contributions (Viswanadhan et al.)
LOGP_FRAGMENTS: Dict[str, Tuple[float, float]] = {
    # Carbons
    "C": (0.20, 12.01),   # Aliphatic CH
    "c": (0.13, 12.01),   # Aromatic C
    # Halogens
    "F": (0.14, 19.00),
    "Cl": (0.60, 35.45),
    "Br": (0.87, 79.90),
    "I": (1.35, 126.90),
    # Oxygen
    "O": (-0.67, 16.00),  # Hydroxyl
    "o": (-0.32, 16.00),  # Aromatic O
    # Nitrogen
    "N": (-1.03, 14.01),  # Amine
    "n": (-0.74, 14.01),  # Aromatic N
    # Sulfur
    "S": (0.54, 32.07),
    "s": (0.27, 32.07),
    # Phosphorus
    "P": (-0.50, 30.97),
}

# Structural motif corrections for logP
LOGP_CORRECTIONS: Dict[str, float] = {
    "COOH": -1.21,    # Carboxylic acid
    "COO":  -0.45,    # Ester
    "C=O":  -0.55,    # Ketone/aldehyde
    "OH":   -0.67,    # Alcohol
    "NH2":  -1.03,    # Primary amine
    "NH":   -0.77,    # Secondary amine
    "N(":   -0.44,    # Tertiary amine
    "S(=O": -1.58,    # Sulfoxide
    "c1":    0.42,    # Benzene ring
}

# hERG cardiotoxicity structural alerts
# Compounds with these features have elevated hERG IC50 risk
HERG_ALERTS: List[Dict] = [
    {"pattern": r"[nN]1ccccc1",   "name": "Piperidine/pyridine nitrogen", "risk": "HIGH",   "ic50_shift": -2.0},
    {"pattern": r"c1ccccc1",      "name": "Unsubstituted phenyl ring",    "risk": "MEDIUM", "ic50_shift": -0.5},
    {"pattern": r"N\(C\)C",       "name": "Tertiary amine",               "risk": "HIGH",   "ic50_shift": -1.5},
    {"pattern": r"Cc1ccccc1",     "name": "Benzyl amine",                 "risk": "MEDIUM", "ic50_shift": -1.0},
    {"pattern": r"[CH2][CH2][nN]","name": "Alkyl-amine chain (2C-N)",     "risk": "HIGH",   "ic50_shift": -1.8},
    {"pattern": r"c1cc2c",        "name": "Naphthalene/fused ring",        "risk": "HIGH",   "ic50_shift": -1.6},
    {"pattern": r"F{2,}",         "name": "Multiple fluorines",           "risk": "LOW",    "ic50_shift":  0.3},
]

# CYP3A4 inhibition substructure patterns
CYP3A4_INHIBITORS: List[Dict] = [
    {"pattern": r"c1ccncc1",   "name": "Pyridine ring",            "strength": "MODERATE"},
    {"pattern": r"n1cccc1",    "name": "Imidazole ring",           "strength": "STRONG"},
    {"pattern": r"N1C=NC=N1",  "name": "Triazole ring",            "strength": "STRONG"},
    {"pattern": r"c1ccc\(O\)", "name": "Para-hydroxyphenyl",       "strength": "WEAK"},
    {"pattern": r"CC\(=O\)N",  "name": "Amide (metabolised)",     "strength": "WEAK"},
    {"pattern": r"OCc1ccccc1", "name": "Benzyl alcohol",          "strength": "MODERATE"},
]

# CYP2D6 inhibition patterns
CYP2D6_INHIBITORS: List[Dict] = [
    {"pattern": r"c1ccccc1N",   "name": "Aminobenzene",         "strength": "MODERATE"},
    {"pattern": r"N1CCCC1",     "name": "Pyrrolidine",          "strength": "MODERATE"},
    {"pattern": r"Cc1ccc\(N\)", "name": "Para-aminotoluene",    "strength": "STRONG"},
]

# Hepatotoxicity structural alerts (Lhasa knowledge rules)
HEPATOTOX_ALERTS: List[Dict] = [
    {"pattern": r"N\(=O\)=O",  "name": "Nitro group",          "severity": "HIGH"},
    {"pattern": r"Nc1ccccc1",  "name": "Aniline derivative",   "severity": "HIGH"},
    {"pattern": r"c1ccc\(Cl\)","name": "Chlorobenzene",        "severity": "MODERATE"},
    {"pattern": r"S\(=O\)\(=O\)","name": "Sulfonyl group",     "severity": "MODERATE"},
    {"pattern": r"C=C-C=O",    "name": "Alpha-beta unsaturated carbonyl (Michael acceptor)", "severity": "HIGH"},
    {"pattern": r"O-N",        "name": "Hydroxylamine",        "severity": "HIGH"},
]

# Polar surface area contributions (PSA) per functional group
PSA_CONTRIBUTIONS: Dict[str, float] = {
    "OH":   20.23,   # Hydroxyl
    "NH2":  26.02,   # Primary amine
    "NH":   17.84,   # Secondary amine
    "N(":   3.24,    # Tertiary amine
    "COOH": 37.30,   # Carboxylic acid
    "C=O":  17.07,   # Carbonyl
    "COO":  26.30,   # Ester
    "S=":   32.09,   # Sulfonyl
    "P=":   9.81,    # Phosphine oxide
}


# ---------------------------------------------------------------------------
# SMILES Parsing Utilities
# ---------------------------------------------------------------------------

def _count_heavy_atoms(smiles: str) -> int:
    """Count non-hydrogen heavy atoms from SMILES."""
    atoms = re.findall(r"[A-Z][a-z]?|\[.*?\]", smiles)
    return len([a for a in atoms if a not in {"H", "[H]"}])


def _estimate_mw(smiles: str) -> float:
    """Estimate molecular weight from SMILES using fragment counts."""
    mw = 0.0
    for symbol, (_, weight) in LOGP_FRAGMENTS.items():
        count = smiles.count(symbol)
        mw += count * weight
    # Add H atoms (rough estimate: 1.008 per heavy atom on average for drug-like)
    heavy = _count_heavy_atoms(smiles)
    mw += heavy * 1.2  # Approximate H contribution
    return round(mw, 2)


def _estimate_logp(smiles: str) -> float:
    """Estimate logP (lipophilicity) using Crippen fragment contribution method."""
    logp = 0.0
    for symbol, (contrib, _) in LOGP_FRAGMENTS.items():
        count = smiles.count(symbol)
        logp += count * contrib
    # Apply functional group corrections
    for group, correction in LOGP_CORRECTIONS.items():
        if group in smiles:
            logp += correction
    return round(logp, 2)


def _count_hbond_donors(smiles: str) -> int:
    """Count H-bond donors (NH, OH groups)."""
    donors = 0
    donors += len(re.findall(r"[NO]H", smiles))
    donors += smiles.count("[NH]") + smiles.count("[NH2]") + smiles.count("[OH]")
    return donors


def _count_hbond_acceptors(smiles: str) -> int:
    """Count H-bond acceptors (N, O atoms)."""
    acceptors = 0
    acceptors += smiles.count("O") + smiles.count("o")
    acceptors += smiles.count("N") + smiles.count("n")
    # Exclude charged atoms
    acceptors -= smiles.count("[N+]") + smiles.count("[O-]")
    return max(0, acceptors)


def _count_rotatable_bonds(smiles: str) -> int:
    """Estimate rotatable bonds from single bonds not in rings."""
    # Count C-C, C-N, C-O single bonds as a proxy
    rot = len(re.findall(r"[A-Za-z]-[A-Za-z]", smiles))
    # Subtract approximate ring bonds (each ring ~3 bonds)
    rings = smiles.count("1") + smiles.count("2")
    ring_bonds = (rings // 2) * 3
    return max(0, rot - ring_bonds)


def _estimate_psa(smiles: str) -> float:
    """Estimate polar surface area (PSA) in Angstrom^2."""
    psa = 0.0
    for group, contribution in PSA_CONTRIBUTIONS.items():
        if group in smiles:
            psa += contribution
    return round(psa, 1)


def _scan_herg(smiles: str) -> Tuple[str, float, List[Dict]]:
    """
    Scan for hERG cardiotoxicity structural alerts.
    Returns: (risk_level, predicted_IC50_uM, matched_alerts)
    """
    matched = []
    total_shift = 0.0

    for alert in HERG_ALERTS:
        if re.search(alert["pattern"], smiles, re.IGNORECASE):
            matched.append(alert)
            total_shift += alert["ic50_shift"]

    # Baseline hERG IC50 ~30 uM for benign compound
    # Negative shift reduces IC50 (more toxic)
    ic50 = 30.0 * (10 ** total_shift)
    ic50 = round(max(ic50, 0.01), 2)

    if ic50 < 1.0:
        risk = "CRITICAL — predicted hERG IC50 < 1 µM"
    elif ic50 < 5.0:
        risk = "HIGH — predicted hERG IC50 < 5 µM"
    elif ic50 < 15.0:
        risk = "MODERATE — predicted hERG IC50 < 15 µM"
    else:
        risk = "LOW — predicted hERG IC50 > 15 µM"

    return risk, ic50, matched


def _scan_cyp(smiles: str) -> Dict[str, str]:
    """Scan for CYP3A4 and CYP2D6 inhibition patterns."""
    cyp3a4_hits = [a["name"] for a in CYP3A4_INHIBITORS if re.search(a["pattern"], smiles, re.IGNORECASE)]
    cyp2d6_hits = [a["name"] for a in CYP2D6_INHIBITORS if re.search(a["pattern"], smiles, re.IGNORECASE)]

    cyp3a4_risk = "INHIBITOR" if len(cyp3a4_hits) >= 2 else "POSSIBLE" if cyp3a4_hits else "UNLIKELY"
    cyp2d6_risk = "INHIBITOR" if len(cyp2d6_hits) >= 2 else "POSSIBLE" if cyp2d6_hits else "UNLIKELY"

    return {
        "CYP3A4": cyp3a4_risk,
        "CYP3A4_features": cyp3a4_hits,
        "CYP2D6": cyp2d6_risk,
        "CYP2D6_features": cyp2d6_hits,
    }


def _predict_bbb(logp: float, mw: float, psa: float, hbd: int) -> Tuple[float, str]:
    """
    Predict blood-brain barrier permeability using Clark model.
    BBB+ predicted if: PSA < 90 Angstrom^2, MW < 400, logP 1-3.
    Returns: (probability, classification)
    """
    score = 0.0
    if psa < 90:   score += 0.35
    if psa < 60:   score += 0.20
    if mw < 400:   score += 0.20
    if mw < 300:   score += 0.10
    if 1.0 <= logp <= 3.0: score += 0.30
    if hbd <= 3:   score += 0.10
    if hbd <= 1:   score += 0.10

    prob = round(min(score, 0.99), 3)
    classification = "BBB+" if prob > 0.6 else "BBB+/- (uncertain)" if prob > 0.35 else "BBB-"
    return prob, classification


def _scan_hepatotox(smiles: str) -> Tuple[str, List[str]]:
    """Scan for hepatotoxicity structural alerts."""
    matched = []
    for alert in HEPATOTOX_ALERTS:
        if re.search(alert["pattern"], smiles, re.IGNORECASE):
            matched.append(f"{alert['name']} [{alert['severity']}]")

    if not matched:
        return "LOW — No hepatotoxicity structural alerts detected", []

    high_count = sum(1 for a in matched if "[HIGH]" in a)
    if high_count >= 2:
        level = "HIGH — Multiple severe hepatotoxicity alerts present"
    elif high_count == 1:
        level = "MODERATE-HIGH — Hepatotoxicity alert requires further testing"
    else:
        level = "MODERATE — Minor hepatotoxicity structural features"

    return level, matched


def _compute_admet_grade(
    ro5_pass: bool, herg_ic50: float, logp: float, psa: float,
    mw: float, hepatotox_matched: List[str], cyp: Dict[str, str],
) -> Tuple[str, str]:
    """
    Compute overall ADMET grade (A/B/C/D/F) and justification.
    """
    demerits = 0
    reasons = []

    if not ro5_pass:
        demerits += 2
        reasons.append("Fails Ro5 (poor oral bioavailability)")
    if herg_ic50 < 1.0:
        demerits += 3
        reasons.append("Critical hERG cardiotoxicity predicted")
    elif herg_ic50 < 5.0:
        demerits += 2
        reasons.append("Elevated hERG cardiotoxicity risk")
    if logp > 5:
        demerits += 1
        reasons.append("High lipophilicity (logP > 5)")
    if logp < 0:
        demerits += 1
        reasons.append("Very low lipophilicity (logP < 0, poor membrane permeation)")
    if psa > 140:
        demerits += 1
        reasons.append("High PSA (>140 Ang^2, poor passive permeation)")
    if len(hepatotox_matched) >= 2:
        demerits += 2
        reasons.append("Multiple hepatotoxicity alerts")
    elif hepatotox_matched:
        demerits += 1
        reasons.append("Hepatotoxicity structural alert")
    if cyp["CYP3A4"] == "INHIBITOR":
        demerits += 1
        reasons.append("CYP3A4 inhibition predicted (drug-drug interaction risk)")

    if demerits == 0:
        grade = "A"
        justification = "Excellent ADMET profile — all properties within optimal ranges."
    elif demerits <= 1:
        grade = "B"
        justification = "Good ADMET profile with minor concerns: " + "; ".join(reasons) + "."
    elif demerits <= 3:
        grade = "C"
        justification = "Moderate ADMET concerns requiring optimisation: " + "; ".join(reasons) + "."
    elif demerits <= 5:
        grade = "D"
        justification = "Poor ADMET profile — significant safety/PK liabilities: " + "; ".join(reasons) + "."
    else:
        grade = "F"
        justification = "FAIL — critical ADMET violations: " + "; ".join(reasons) + "."

    return grade, justification


def _suggest_modifications(logp: float, mw: float, psa: float, herg_ic50: float) -> List[str]:
    """Suggest structural modifications to improve ADMET grade."""
    suggestions = []
    if logp > 5:
        suggestions.append("Reduce lipophilicity: add polar groups (OH, COOH) or remove alkyl chains")
    if logp < 0:
        suggestions.append("Increase lipophilicity: methylate polar groups or add aromatic ring")
    if mw > 500:
        suggestions.append("Reduce molecular weight: remove redundant substituents or use bioisostere")
    if psa > 140:
        suggestions.append("Reduce PSA: mask H-bond donors via methylation or prodrug strategy")
    if herg_ic50 < 5:
        suggestions.append("Reduce hERG risk: remove basic nitrogen, add F at para position, or reduce lipophilicity")
    if not suggestions:
        suggestions.append("No major structural modifications indicated — compound shows promising ADMET profile")
    return suggestions


# ---------------------------------------------------------------------------
# Main API entry point
# ---------------------------------------------------------------------------

def run_admet_screen(
    smiles: str,
    compound_name: str = "Unknown",
    therapeutic_area: str = "cardiac",
) -> Dict:
    """
    Full ADMET safety screening from SMILES molecular string.

    Args:
        smiles: SMILES molecular representation of the drug candidate
        compound_name: Human-readable name
        therapeutic_area: 'cardiac' | 'neurological' | 'oncology' | 'general'

    Returns:
        Complete ADMET profile dict
    """
    # ---- Lipinski descriptors ----
    mw = _estimate_mw(smiles)
    logp = _estimate_logp(smiles)
    hbd = _count_hbond_donors(smiles)
    hba = _count_hbond_acceptors(smiles)
    rot = _count_rotatable_bonds(smiles)
    psa = _estimate_psa(smiles)

    # ---- Ro5 check ----
    ro5_violations = []
    if mw > 500:    ro5_violations.append(f"MW={mw:.0f} Da > 500")
    if logp > 5:    ro5_violations.append(f"logP={logp} > 5")
    if hbd > 5:     ro5_violations.append(f"HBD={hbd} > 5")
    if hba > 10:    ro5_violations.append(f"HBA={hba} > 10")
    ro5_pass = len(ro5_violations) <= 1  # 1 violation allowed (Pfizer rule)

    # ---- Veber rules ----
    veber_pass = (rot <= 10) and (psa <= 140)
    veber_violations = []
    if rot > 10: veber_violations.append(f"Rotatable bonds={rot} > 10")
    if psa > 140: veber_violations.append(f"PSA={psa} > 140 Ang^2")

    # ---- hERG cardiotoxicity ----
    herg_risk, herg_ic50, herg_alerts = _scan_herg(smiles)

    # ---- CYP inhibition ----
    cyp_profile = _scan_cyp(smiles)

    # ---- BBB permeability ----
    bbb_prob, bbb_class = _predict_bbb(logp, mw, psa, hbd)

    # ---- Hepatotoxicity ----
    hepatotox_level, hepatotox_alerts = _scan_hepatotox(smiles)

    # ---- Overall ADMET grade ----
    grade, grade_justification = _compute_admet_grade(
        ro5_pass, herg_ic50, logp, psa, mw, hepatotox_alerts, cyp_profile
    )

    # ---- Structural modification suggestions ----
    suggestions = _suggest_modifications(logp, mw, psa, herg_ic50)

    # ---- Cardiac-specific risk amplification ----
    cardiac_note = None
    if therapeutic_area == "cardiac" and herg_ic50 < 10:
        cardiac_note = (
            f"WARNING: For cardiac applications, hERG IC50 = {herg_ic50} µM is concerning. "
            f"Recommend in vitro APD90 patch-clamp validation before progressing."
        )

    return {
        "compound": {
            "name": compound_name,
            "smiles": smiles,
            "therapeutic_area": therapeutic_area,
        },
        "molecular_properties": {
            "molecular_weight_da": mw,
            "logP": logp,
            "h_bond_donors": hbd,
            "h_bond_acceptors": hba,
            "rotatable_bonds": rot,
            "polar_surface_area_angstrom2": psa,
        },
        "lipinski_ro5": {
            "pass": ro5_pass,
            "violations": ro5_violations,
            "oral_bioavailability_prediction": "LIKELY" if ro5_pass else "UNLIKELY",
        },
        "veber_rules": {
            "pass": veber_pass,
            "violations": veber_violations,
            "intestinal_permeability_prediction": "GOOD" if veber_pass else "POOR",
        },
        "herg_cardiotoxicity": {
            "risk_level": herg_risk,
            "predicted_ic50_um": herg_ic50,
            "structural_alerts": [a["name"] for a in herg_alerts],
            "cardiotoxicity_flag": herg_ic50 < 5.0,
        },
        "cyp_inhibition": cyp_profile,
        "bbb_permeability": {
            "probability": bbb_prob,
            "classification": bbb_class,
            "cns_penetration_expected": bbb_class == "BBB+",
        },
        "hepatotoxicity": {
            "risk_level": hepatotox_level,
            "structural_alerts": hepatotox_alerts,
        },
        "admet_grade": grade,
        "admet_grade_justification": grade_justification,
        "structural_modification_suggestions": suggestions,
        "cardiac_specific_note": cardiac_note,
        "summary": (
            f"Compound '{compound_name}' — ADMET Grade: {grade}. "
            f"MW={mw:.0f} Da, logP={logp}, PSA={psa} Ang^2. "
            f"Ro5: {'PASS' if ro5_pass else 'FAIL'}. "
            f"hERG IC50: {herg_ic50} µM ({herg_risk.split('—')[0].strip()}). "
            f"CYP3A4: {cyp_profile['CYP3A4']}. "
            f"BBB: {bbb_class}."
        ),
    }
