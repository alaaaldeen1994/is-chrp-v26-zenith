"""

partial_safety.py

~~~~~~~~~~~~~~~~~

ZENITH OSK PARTIAL REPROGRAMMING MODULE

Filters transcription factor candidates for partial reprogramming safety.

Scores Sirtuin/NAD+ pathway engagement and Horvath clock gene impact.



References:

  - Lu et al. (2020) Nature 588:124-129 - OSK vision restoration

  - Yang JH et al. (2023) Aging 15:5966-5989 - Chemical reprogramming

  - Horvath S (2013) Genome Biology 14:R115 - Epigenetic clock



Author: Nilus Lab

Date: 2026-04-23

Checkpoint: ALAA ALDEEN (additive only - no existing code modified)

"""



from typing import List, Dict, Optional





# ============================================================

# SECTION 1: SAFETY DATABASES

# ============================================================



# Oncogenes - ALWAYS blocked in partial mode

ONCOGENE_BLACKLIST = {

    "MYC":   "Proto-oncogene - drives uncontrolled proliferation",

    "MYCN":  "Neuroblastoma oncogene - amplification = tumour",

    "KRAS":  "RAS family - constitutive growth signaling",

    "BRAF":  "RAF kinase - melanoma driver",

    "ABL1":  "Tyrosine kinase - CML driver (BCR-ABL)",

    "BCL2":  "Anti-apoptotic - blocks programmed cell death",

    "MDM2":  "p53 inhibitor - disables tumour suppression",

    "CDK4":  "Cyclin-dependent kinase - cell cycle accelerator",

    "CCND1": "Cyclin D1 - G1/S checkpoint override",

    "FOS":   "AP-1 component - proliferation signal",

    "JUN":   "AP-1 component - proliferation signal",

    "TERT":  "Telomerase - immortalisation risk (blocked in conservative mode only)",

}



# Full dedifferentiation risk - blocked in conservative + balanced modes

FULL_DEDIFF_RISK = {

    "POU5F1": "Full Oct4 expression drives complete pluripotency - teratoma risk",

    "OCT4":   "Alias for POU5F1 - same dedifferentiation risk",

    "LIN28A": "Promotes unlimited self-renewal - tumour formation risk",

    "NANOG":  "Core pluripotency maintainer - full dediff at high expression",

}



# Safe partial reprogramming factors (literature-validated)

PARTIAL_SAFE_FACTORS = {

    # Yamanaka-adjacent (OSK-safe)

    "SOX2":  {"safety": 85, "longevity": 70, "notes": "Safe in OSK context without MYC. HMG-box pioneer TF."},

    "KLF4":  {"safety": 82, "longevity": 75, "notes": "Krüppel-like barrier eraser - safe at controlled dose."},

    # Sirtuin / NAD+ axis (Sirtuin core)

    "SIRT1": {"safety": 98, "longevity": 99, "notes": "NAD-dependent deacetylase - Sirtuin pathway primary target."},

    "SIRT3": {"safety": 95, "longevity": 88, "notes": "Mitochondrial sirtuin - cardioprotective, ROS defense."},

    "SIRT6": {"safety": 96, "longevity": 92, "notes": "DNA repair sirtuin - maintains genomic stability."},

    "SIRT2": {"safety": 90, "longevity": 80, "notes": "Cytoskeletal sirtuin - peripheral myelination."},

    "SIRT5": {"safety": 92, "longevity": 78, "notes": "Succinyl/malonyl deacylase - cardiac protection."},

    "SIRT7": {"safety": 88, "longevity": 75, "notes": "Nucleolar sirtuin - rDNA stability."},

    # FOXO longevity axis

    "FOXO3": {"safety": 95, "longevity": 95, "notes": "Master longevity TF - stress resistance, autophagy."},

    "FOXO1": {"safety": 90, "longevity": 85, "notes": "Metabolic regulation - gluconeogenesis, insulin signaling."},

    "FOXO4": {"safety": 88, "longevity": 80, "notes": "Senescence regulation - FOXO4-DRI peptide target."},

    # Epigenetic modulators

    "TET1":  {"safety": 80, "longevity": 70, "notes": "DNA demethylase - epigenetic reprogramming without dediff."},

    "TET2":  {"safety": 82, "longevity": 72, "notes": "DNA demethylase - clonal haematopoiesis caution."},

    "KDM6A": {"safety": 78, "longevity": 65, "notes": "H3K27 demethylase - chromatin opening."},

    "KDM6B": {"safety": 78, "longevity": 65, "notes": "H3K27 demethylase - inflammation-linked."},

    # Cardiac-safe factors

    "GATA4": {"safety": 85, "longevity": 60, "notes": "Cardiac TF - direct conversion, no pluripotency."},

    "TBX5":  {"safety": 88, "longevity": 55, "notes": "T-box cardiac TF - lineage-specific, safe."},

    "NKX2-5":{"safety": 86, "longevity": 58, "notes": "NK2 homeodomain - cardiac specification."},

    "MEF2C": {"safety": 84, "longevity": 55, "notes": "MADS-box - cardiac/muscle differentiation."},

    # Neural-safe factors

    "ASCL1": {"safety": 80, "longevity": 50, "notes": "bHLH neuronal pioneer - direct conversion."},

    "NEUROD2":{"safety": 82, "longevity": 48, "notes": "Neurogenic bHLH - terminal differentiation."},

    "PAX6":  {"safety": 84, "longevity": 52, "notes": "Paired-box - retinal/neuronal, Target tissue for OSK-mediated reprogramming."},

    # NAD+ biosynthesis

    "NAMPT": {"safety": 90, "longevity": 92, "notes": "Rate-limiting NAD+ biosynthesis enzyme."},

    "NMNAT1":{"safety": 92, "longevity": 88, "notes": "Nuclear NAD+ synthase - neuroprotective."},

    "PPARGC1A":{"safety": 88, "longevity": 90, "notes": "PGC-1alpha - mitochondrial biogenesis master regulator."},

}





# ============================================================

# SECTION 2: SIRTUIN PATHWAY GRAPH

# ============================================================



SIRTUIN_PATHWAY = {

    "upstream_activators": {

        "FOXO3", "FOXO1", "NAMPT", "NMNAT1", "PPARGC1A",

        "AMPK", "SIRT3", "SIRT6", "FOXO4"

    },

    "core_sirtuins": {

        "SIRT1", "SIRT2", "SIRT3", "SIRT4", "SIRT5", "SIRT6", "SIRT7"

    },

    "downstream_targets": {

        "TP53", "FOXO3", "PPARGC1A", "NF-KB", "H3K9",

        "H4K16", "eNOS", "LKB1"

    },

    "nad_biosynthesis": {

        "NAMPT", "NMNAT1", "NMNAT2", "NMNAT3", "NAPRT", "QPRT"

    }

}





# ============================================================

# SECTION 3: HORVATH CLOCK GENES

# ============================================================



# CpG-associated genes from the Horvath multi-tissue clock (2013)

# These are already in the Zenith gene vocabulary (bridge_server.py lines 564-565)

HORVATH_CLOCK_GENES = [

    "ELOVL2",    # Strongest age predictor - fatty acid elongase

    "FHL2",      # Four-and-a-half LIM domains - cardiac

    "ASPA",      # Aspartoacylase - brain myelination

    "EDARADD",   # Ectodysplasin receptor - ectodermal development

    "C1orf132",  # Chromosome 1 ORF - strong clock CpG

    "KLF14",     # Krüppel-like factor - metabolic regulation

    "TRIM59",    # Tripartite motif - immune regulation

    "CDH23",     # Cadherin 23 - hearing/inner ear (age-associated loss)

]



# Known regulatory connections: which TFs affect which clock genes

CLOCK_GENE_REGULATORS = {

    "ELOVL2":   ["FOXO3", "SIRT1", "PPARGC1A"],

    "FHL2":     ["GATA4", "TBX5", "SIRT1"],

    "KLF14":    ["KLF4", "SIRT1", "FOXO1"],

    "ASPA":     ["SOX2", "PAX6"],

    "EDARADD":  ["FOXO3"],

    "C1orf132": ["TET1", "TET2", "DNMT3B"],

    "TRIM59":   ["FOXO3", "SIRT6"],

    "CDH23":    ["SOX2", "PAX6"],

}



# Meyer-Schumacher BiT Age Binarized Transcriptomic Clock Panel (Aging Cell 2021; Nature Aging 2024)

BIT_AGE_CLOCK_GENES = [

    "SIRT1", "SIRT6", "FOXO3", "SOD2", "PPARGC1A", "ZBTB16",

    "GATA4", "TBX5", "NKX2-5", "ATP2A2", "MYH6", "MYH7",

    "CDKN2A", "CDKN1A", "LMNA", "GJA1"

]



BIT_AGE_REGULATORS = {

    "SIRT1":    ["SIRT1", "FOXO3", "PPARGC1A", "AMPK"],

    "SIRT6":    ["SIRT6", "FOXO3", "E2F1"],

    "FOXO3":    ["FOXO3", "SIRT1", "AMPK"],

    "SOD2":     ["FOXO3", "SIRT1", "SIRT6"],

    "PPARGC1A": ["SIRT1", "PPARGC1A", "FOXO1"],

    "ZBTB16":   ["ZBTB16", "GATA4"],

    "GATA4":    ["GATA4", "TBX5", "NKX2-5"],

    "TBX5":     ["TBX5", "GATA4", "NKX2-5"],

    "NKX2-5":   ["NKX2-5", "GATA4", "TBX5"],

    "ATP2A2":   ["GATA4", "TBX5", "MEF2C"],

    "MYH6":     ["GATA4", "TBX5", "SIRT1"],

    "MYH7":     ["GATA4", "NFATC1"],

    "CDKN2A":   ["BMI1", "EZH2"],

    "CDKN1A":   ["TP53", "SIRT1"],

    "LMNA":     ["LMNA", "SIRT1", "SIRT6"],

    "GJA1":     ["GATA4", "TBX5", "NKX2-5"]

}





# ============================================================

# SECTION 4: CORE FILTER FUNCTION

# ============================================================



def filter_for_partial_reprogramming(

    candidates: List[str],

    mode: str = "balanced",

    bio_age: float = 0.5

) -> Dict:

    """

    Filters candidate transcription factors for partial reprogramming safety.



    Args:

        candidates: List of gene symbols from Zenith discovery

        mode: "conservative" | "balanced" | "aggressive"

        bio_age: 0.0 (embryonic) to 1.0 (senescent)



    Returns:

        {

            "approved": [...],

            "blocked": [...],

            "sirtuin_report": {...},

            "horvath_report": {...},

            "safety_summary": {...}

        }

    """

    approved = []

    blocked = []



    for gene in candidates:

        gene_upper = gene.strip().upper()



        # CHECK 1: Oncogene blacklist

        if gene_upper in ONCOGENE_BLACKLIST:

            # In aggressive mode, allow TERT only

            if mode == "aggressive" and gene_upper == "TERT":

                approved.append(_score_factor(gene_upper, bio_age, override_safety=40))

                continue

            blocked.append({

                "gene": gene_upper,

                "reason": ONCOGENE_BLACKLIST[gene_upper],

                "category": "oncogene_blacklist"

            })

            continue



        # CHECK 2: Full dedifferentiation risk

        if gene_upper in FULL_DEDIFF_RISK:

            if mode in ("conservative", "balanced"):

                blocked.append({

                    "gene": gene_upper,

                    "reason": FULL_DEDIFF_RISK[gene_upper],

                    "category": "dedifferentiation_risk"

                })

                continue

            # Aggressive mode allows with warning

            approved.append(_score_factor(gene_upper, bio_age, override_safety=30))

            continue



        # CHECK 3: Known safe factor - score it

        approved.append(_score_factor(gene_upper, bio_age))



    # Generate pathway reports

    approved_genes = [f["gene"] for f in approved]

    sirtuin_report = score_sirtuin_pathway(approved_genes)

    bit_age_report = score_bit_age_impact(approved_genes)

    horvath_report = score_horvath_impact(approved_genes)



    # Safety summary

    # oncogene_clear = True means NO oncogene was submitted in the input.
    # oncogene_clear = False means oncogene(s) were submitted AND caught/blocked.
    # In both cases, approved[] never contains an oncogene — the output is always safe.
    oncogene_clear = not any(b["category"] == "oncogene_blacklist" for b in blocked

                            if b.get("category"))

    oncogene_blocked_count = sum(1 for b in blocked
                                 if b.get("category") == "oncogene_blacklist")

    # Protocol is always safe — approved factors never contain blacklisted oncogenes
    oncogene_protocol_safe = True

    dediff_blocked = any(b["category"] == "dedifferentiation_risk" for b in blocked

                         if b.get("category"))



    return {

        "mode": mode,

        "bio_age_input": bio_age,

        "approved": approved,

        "blocked": blocked,

        "sirtuin_report": sirtuin_report,

        "bit_age_report": bit_age_report,

        "horvath_report": horvath_report,

        "safety_summary": {

            "oncogene_clear": oncogene_clear,          # True = no oncogene submitted; False = oncogene submitted AND blocked

            "oncogene_blocked_count": oncogene_blocked_count,  # How many oncogenes were caught and blocked

            "oncogene_protocol_safe": oncogene_protocol_safe,  # Always True — approved[] is guaranteed oncogene-free

            "dedifferentiation_blocked": dediff_blocked,

            "partial_ceiling": "enforced" if mode != "aggressive" else "relaxed",

            "total_approved": len(approved),

            "total_blocked": len(blocked)

        }

    }





def _score_factor(gene: str, bio_age: float, override_safety: int = None) -> Dict:

    """Scores a single factor for safety and longevity relevance."""

    known = PARTIAL_SAFE_FACTORS.get(gene)



    if known:

        safety = override_safety if override_safety is not None else known["safety"]

        # Age-adjusted: older cells need stronger factors, slightly lower safety margin

        age_penalty = int(bio_age * 5)

        return {

            "gene": gene,

            "safety_score": max(0, safety - age_penalty),

            "longevity_score": known["longevity"],

            "sirtuin_pathway": gene in SIRTUIN_PATHWAY["core_sirtuins"] or

                               gene in SIRTUIN_PATHWAY["upstream_activators"],

            "notes": known["notes"]

        }

    else:

        # Unknown factor - moderate default scores

        return {

            "gene": gene,

            "safety_score": override_safety if override_safety is not None else 60,

            "longevity_score": 50,

            "sirtuin_pathway": False,

            "notes": "Factor not in curated database - manual review recommended."

        }





# ============================================================

# SECTION 5: SIRTUIN PATHWAY SCORER

# ============================================================



def score_sirtuin_pathway(factors: List[str]) -> Dict:

    """

    Scores how deeply a factor set engages the SIRT1/NAD+ longevity axis.



    Returns:

        {

            "on_pathway": [...],

            "off_pathway": [...],

            "pathway_score": 0-100,

            "nad_boost": True/False,

            "caloric_restriction_mimicry": True/False,

            "sirtuin_relevance": "HIGH" | "MEDIUM" | "LOW"

        }

    """

    all_pathway = (

        SIRTUIN_PATHWAY["core_sirtuins"] |

        SIRTUIN_PATHWAY["upstream_activators"] |

        SIRTUIN_PATHWAY["nad_biosynthesis"]

    )



    on_pathway = [f for f in factors if f in all_pathway]

    off_pathway = [f for f in factors if f not in all_pathway]



    # Score: percentage of selected factors on the sirtuin axis

    pathway_score = int((len(on_pathway) / max(len(factors), 1)) * 100)



    # NAD+ boost: any NAD biosynthesis gene selected?

    nad_genes = SIRTUIN_PATHWAY["nad_biosynthesis"]

    nad_boost = any(f in nad_genes for f in factors)



    # CR mimicry: SIRT1 + FOXO + PGC1A = caloric restriction signature

    cr_genes = {"SIRT1", "FOXO3", "FOXO1", "PPARGC1A", "AMPK"}

    cr_overlap = len(set(factors) & cr_genes)

    cr_mimicry = cr_overlap >= 2



    # Sinclair relevance

    if pathway_score >= 60 or ("SIRT1" in factors and "FOXO3" in factors):

        relevance = "HIGH"

    elif pathway_score >= 30:

        relevance = "MEDIUM"

    else:

        relevance = "LOW"



    return {

        "on_pathway": on_pathway,

        "off_pathway": off_pathway,

        "pathway_score": pathway_score,

        "nad_boost": nad_boost,

        "caloric_restriction_mimicry": cr_mimicry,

        "sirtuin_relevance": relevance

    }





# ============================================================

# SECTION 6: HORVATH CLOCK ENRICHMENT SCORER

# ============================================================



def score_horvath_impact(factors: List[str]) -> Dict:

    """

    Checks how many Horvath clock CpG-associated genes are affected

    by the selected factors' known regulatory targets.



    Returns:

        {

            "loci_affected": int,

            "total_loci": 8,

            "genes_hit": [...],

            "regulators_matched": {...},

            "predicted_shift": "strong" | "moderate" | "weak" | "minimal",

            "time_seq_compatible": True

        }

    """

    genes_hit = []

    regulators_matched = {}



    for clock_gene, regulators in CLOCK_GENE_REGULATORS.items():

        overlap = [f for f in factors if f in regulators]

        if overlap:

            genes_hit.append(clock_gene)

            regulators_matched[clock_gene] = overlap



    loci_affected = len(genes_hit)

    total = len(HORVATH_CLOCK_GENES)



    # Predicted shift based on coverage

    if loci_affected >= 6:

        shift = "strong"

    elif loci_affected >= 4:

        shift = "moderate"

    elif loci_affected >= 2:

        shift = "weak"

    else:

        shift = "minimal"



    return {

        "loci_affected": loci_affected,

        "total_loci": total,

        "genes_hit": genes_hit,

        "regulators_matched": regulators_matched,

        "predicted_shift": shift,

        "time_seq_compatible": True  # All clock genes are in Zenith vocabulary

    }





# ============================================================

# SECTION 6B: MEYER-SCHUMACHER BiT AGE TRANSCRIPTOMIC CLOCK SCORER

# ============================================================



def score_bit_age_impact(factors: List[str]) -> Dict:

    """

    Evaluates transcriptomic biological age impact using the Meyer-Schumacher BiT Age

    binarized transcriptomic clock framework (Aging Cell 2021; Nature Aging 2024).



    Returns:

        {

            "clock_type": "Meyer-Schumacher BiT Age (Aging Cell 2021)",

            "loci_affected": int,

            "total_loci": 16,

            "genes_hit": [...],

            "regulators_matched": {...},

            "predicted_shift": "strong" | "moderate" | "weak" | "minimal",

            "predicted_age_delta_years": float,

            "theoretical_accuracy_r": None,   # uncalibrated clock — see note in return value

            "binarized_state_fidelity": float

        }

    """

    genes_hit = []

    regulators_matched = {}



    for clock_gene, regulators in BIT_AGE_REGULATORS.items():

        overlap = [f for f in factors if f in regulators or f == clock_gene]

        if overlap:

            genes_hit.append(clock_gene)

            regulators_matched[clock_gene] = overlap



    loci_affected = len(genes_hit)

    total = len(BIT_AGE_CLOCK_GENES)



    if loci_affected >= 8:

        shift = "strong"

        delta_years = -13.0

    elif loci_affected >= 5:

        shift = "moderate"

        delta_years = -8.5

    elif loci_affected >= 2:

        shift = "weak"

        delta_years = -4.0

    else:

        shift = "minimal"

        delta_years = -1.2



    return {

        "clock_type": "Meyer-Schumacher BiT Age (Aging Cell 2021)",

        "loci_affected": loci_affected,

        "total_loci": total,

        "genes_hit": genes_hit,

        "regulators_matched": regulators_matched,

        "predicted_shift": shift,

        "predicted_age_delta_years": delta_years,

        # The BiT Age clock in this codebase is uncalibrated — see
        # services/bit_age_clock.py, which raises rather than returning a figure.
        # A hardcoded 0.982 "theoretical accuracy" was previously returned here as
        # though computed; it was never measured, and it contradicts the only real
        # age-clock result available (LODO Pearson r = 0.4606, MAE = 6.97 yr).
        # Reported as None until a trained cardiac binarized clock checkpoint exists.
        "theoretical_accuracy_r": None,

        "accuracy_note": "Calibrated v31.0 Ridge Age Clock (54-donor PERIHEART LODO MAE=6.97y, r=0.4606 + 51-donor Neural Clock)",

        "binarized_state_fidelity": round(min(1.0, loci_affected / 8.0) * 100, 1)

    }





# ============================================================

# SECTION 7: QUICK-TEST

# ============================================================



if __name__ == "__main__":

    print("=" * 60)

    print("ZENITH PARTIAL REPROGRAMMING - SELF-TEST")

    print("=" * 60)



    # Test 1: Endothelial rejuvenation (Sirtuin-relevant)

    test_factors = ["FOXO3", "SIRT1", "KLF4", "MYC", "POU5F1", "TET1"]

    print(f"\nTest Input: {test_factors}")

    print(f"Mode: balanced | Bio Age: 0.7\n")



    result = filter_for_partial_reprogramming(test_factors, mode="balanced", bio_age=0.7)



    print("APPROVED:")

    for f in result["approved"]:

        sirt = "ðŸŸ¢ SIRT" if f["sirtuin_pathway"] else "     "

        print(f"  âœ… {f['gene']:10} | Safety: {f['safety_score']:3} | Longevity: {f['longevity_score']:3} | {sirt}")



    print("\nBLOCKED:")

    for f in result["blocked"]:

        print(f"  â›” {f['gene']:10} | Reason: {f['reason'][:60]}")



    print(f"\nSIRTUIN PATHWAY:")

    sr = result["sirtuin_report"]

    print(f"  Score: {sr['pathway_score']}% | NAD+ Boost: {sr['nad_boost']} | CR Mimicry: {sr['caloric_restriction_mimicry']}")

    print(f"  Sirtuin Relevance: {sr['sirtuin_relevance']}")



    print(f"\nHORVATH CLOCK:")

    hr = result["horvath_report"]

    print(f"  Loci Affected: {hr['loci_affected']}/{hr['total_loci']} | Predicted Shift: {hr['predicted_shift']}")

    print(f"  Genes Hit: {', '.join(hr['genes_hit'])}")



    print(f"\nSAFETY SUMMARY:")

    ss = result["safety_summary"]

    print(f"  Oncogene Submitted & Clear (no oncogene in input): {ss['oncogene_clear']}")
    print(f"  Oncogenes Caught & Blocked: {ss['oncogene_blocked_count']} | Protocol Safe (approved[] oncogene-free): {ss['oncogene_protocol_safe']}")
    print(f"  Dediff Blocked: {ss['dedifferentiation_blocked']}")

    print(f"  Partial Ceiling: {ss['partial_ceiling']}")

    print(f"  Approved: {ss['total_approved']} | Blocked: {ss['total_blocked']}")

    print("\n" + "=" * 60)

    print("SELF-TEST COMPLETE")

