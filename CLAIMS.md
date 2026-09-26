# Zenith Platform Scientific Claims & Empirical Evidence Base

## 1. Overview & Research-Use-Only (RUO) Boundary
This document establishes the empirical validation status, calibration limits, and formal provenance disclosures for computational models within the Zenith platform (`www.niluslab.com`). 

All software, models, and endpoints are designated strictly for **Research Use Only (RUO)**. They do not constitute a medical device, clinical diagnostic, or validated therapeutic intervention protocol.

---

## 2. Epigenetic & Transcriptomic Clock Validation

### 2.1 Internal Validation: MAGNet Human Heart Cohort
Model evaluation on human cardiac tissue profiles from the Myocardial Applied Genomics Network (MAGNet) cohort establishes the following internal performance benchmarks:
* **Coefficient of Determination ($R^2$):** $0.418$
* **Internal Mean Absolute Error (MAE):** $8.27\text{ years}$

### 2.2 External Validation: GTEx Left Ventricle Cohort
External cross-cohort validation was conducted on human left ventricle bulk RNA-seq samples from the Genotype-Tissue Expression (GTEx) project to evaluate generalizability under real-world technical and platform shifts:
* **Direct Transfer MAE (Uncalibrated):** $90.05\text{ years}$  
  *Direct zero-shot application exhibits severe systematic drift caused by unaligned sequencing chemistry, library preparation, and platform-specific baseline expression offsets.*
* **Mean-Calibrated External MAE:** $9.51\text{ years}$
* **Trivial Constant-Mean Donor Baseline MAE:** $8.38\text{ years}$
* **Empirical Finding:** When tested on the external GTEx left ventricle cohort, the mean-calibrated model ($9.51\text{ yr}$) does not outperform the constant-mean donor baseline ($8.38\text{ yr}$). Out-of-cohort chronological age point-prediction requires rigorous cross-platform transfer calibration prior to any biological interpretation.

### 2.3 Single-Cell Atrial Cohort: PERIHEART Leave-One-Donor-Out (LODO)
On $N = 54$ living surgical donors in the PERIHEART atlas ($88,561$ right atrial appendage cardiomyocytes; decade-binned targets):
* **LODO Ridge Clock MAE:** $6.97\text{ years}$ ($r = 0.4606$, $p = 4.57 \times 10^{-4}$; permutation null MAE $= 9.05 \pm 0.80\text{ yr}$, empirical $p = 0.0030$).
* **Constant-Median Baseline MAE:** $7.59\text{ years}$ (clock improvement $= 0.62\text{ yr}$ / $8.15\%$, paired $t = -0.83$, $p = 0.41$, not statistically significant).
* **Quantization Floor:** $2.50\text{ years}$ due to 10-year age-binning in source donor metadata.
* **Tissue Scope Disclosure:** Evaluated exclusively on right atrial appendage tissue; zero ventricular cardiomyocytes are present in the PERIHEART cohort.

---

## 3. Replicated 16-Gene Aging Core
Cross-cohort replication analysis across two independent adult human single-cell and single-nucleus cardiac datasets—**Litviňuková et al.** (*Nature* 2020; $486,134$ cells, $14$ post-mortem donors) and **PERIHEART** (Kanemaru et al., *Nature* 2023; $392,819$ cells, $54$ living surgical donors)—identified a 16-gene core showing concordant, unconfounded directional shifts with donor age:
* **Key Core Markers:**
  * **`EDA2R`** (Ectodysplasin A2 receptor): Robustly up-regulated with chronological age ($p < 0.001$), acting as a p53-responsive mediator of cellular senescence and apoptosis in cardiovascular tissue.
  * **`PTCHD4`** (Patched domain containing 4): Demonstrates consistent down-regulation with advancing chronological age across independent cohorts.
* **Confounder Disclosure:** Multiple putative age markers identified in naive cell-level correlations (e.g. `HSPB1`, `CRYAB`, `FOS`, `JUN`) lose significance when adjusted for processing center (Sanger vs. Harvard) and donor-level pseudobulking, reflecting technical dissociation stress rather than intrinsic biological senescence.

---

## 4. Provenance Layer Failure & Remediation Disclosure

### 4.1 Root Cause & Decommissioned Artifacts
Audits of legacy pipeline code revealed critical provenance failures:
1. **Synthetic Perturbation & Fabricated Metrics:** Legacy scripts `run_zenith_screening_pipeline.py` and `simulate_perturbation()` utilized heuristic mathematical functions rather than wet-lab or physical simulations. Outputs such as `zenith_screening_audit.csv` and `screen_output.csv` generated fabricated rejuvenation shifts, simulated compound synergies, and synthetic screening scores.
2. **Prescription Drug Dosing Panel:** The web interface and backend previously included an unapproved prescription drug dosing simulator coupled to synthetic pharmacokinetic formulas and unvalidated epigenetic clock shifts.
3. **Synthetic PDB Structure Fallback:** When external structural biology endpoints (ESMFold) timed out, legacy code synthesized an idealized poly-alanine alpha helix PDB structure rather than raising an error.

### 4.2 Remediation Actions Taken (Track 1 Production Hotfix)
* **Quarantine:** All legacy screening code and synthetic CSV files have been removed from the repository root and quarantined under `quarantine/track2/`.
* **Complete Removal of Drug Dosing:** All prescription compound models, sliders, event listeners, and PK/PD simulations have been eliminated from `index.html`, `js/script.js`, `services/pkpd_engine.py`, and `services/multiomics_service.py`.
* **Endpoint Decommissioning:** Uncalibrated routes (`/api/v1/clinical/predict/perturbation`, `/api/v1/predict/perturbation`, `/api/v1/safety/audit`, `/api/v1/trials/run`, `/run_virtual_trial`, `/api/v2/multiomics/integrate`, and `/api/v1/neural/dual_comparator`) have been decommissioned and respond with `HTTP 410 Gone`.
* **Fallback Disabling:** Synthetic PDB generation in `services/structural_folder.py` has been disabled (`settings.ESMFOLD_FALLBACK_ENABLED = False`). Failed structure requests return explicit provider error states.
* **Clock Safeguards:** The cardiac ensemble clock requires empirical methylation array inputs; in the absence of valid array data, synthetic probe generation is bypassed, and the service returns `rejuvenation_delta_years = None` alongside the empirical PERIHEART LODO baseline.

---

## 5. Public Claims Evidence Pack & Platform Record Audits

| Date | Public Claim | Stated Metric / Statement | Empirical Investigation & Findings | Source / Verification Location | Audit Date | Status |
|---|---|---|---|---|---|---|
| **28 Mar 2026** | User Traction | "5,000+ users onboarded" | **Zero (0) registered users.** Firebase Authentication user registry audit confirmed zero registered consumer/external user accounts exist in the production identity database (`nilus-lab`). No user credential records exist in local databases. | Firebase Console (`https://console.firebase.google.com/project/nilus-lab/authentication/users`) & SQLite database audit | 26 Sep 2026 | **Refuted / Fabricated** |
| **22 Apr 2026** | Structure Prediction | "AlphaFold 3 ipTM 0.82 / 0.81 / 0.69" | **No AF3 execution infrastructure.** AlphaFold 3 was not executed on platform infrastructure (DeepMind AlphaFold Server terms prohibit non-academic/commercial automated execution). Only JSON input manifests were formatted; no output coordinates or ipTM scores were generated by AF3. | Codebase inspection & SQLite structure logs | 26 Sep 2026 | **Refuted / Unexecuted** |
| **20 May / 23 May 2026** | Simulation Provenance | "Computed, not hallucinated" · "This is not a mock" | **Rigged Heuristic Generators.** Values presented on platform originated from uncalibrated polynomial functions, hardcoded arrays, and heuristic formulas in `run_zenith_screening_pipeline.py` and `simulate_perturbation()`. | Quarantine directory (`quarantine/track2/`) | 26 Sep 2026 | **Refuted / Heuristic** |
| **9 Jun 2026** | Corpus Scope | "500,000 real cells from the Human Cell Atlas & PERIHEART" | **PERIHEART Absent from Foundation Corpus.** Foundation scVI model was trained on 1,962,128 cells across 14 CELLxGENE cohorts; PERIHEART was evaluated separately in atrial benchmarks and was not part of the foundation training corpus. | Training corpus metadata registry | 26 Sep 2026 | **Refuted / Misattributed** |
| **23 Sep 2026** | Platform Traceability | "Traceable to its underlying models" | **Fabricated Outputs.** On 23 Sep 2026, the live platform served hardcoded prescription drug clock shifts, synthetic fallback PDB structures, and uncalibrated clinical trial endpoints. | Production repository audit | 26 Sep 2026 | **Refuted / Stale Deployment** |

