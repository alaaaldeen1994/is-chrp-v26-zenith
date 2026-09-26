# Zenith Platform Scientific Claims & Empirical Evidence Base

## 1. Overview & Research-Use-Only (RUO) Boundary
This document establishes the empirical validation status, calibration limits, and formal provenance disclosures for computational models within the Zenith platform (`www.niluslab.com`). 

All software, models, and endpoints are designated strictly for **Research Use Only (RUO)**. They do not constitute a medical device, clinical diagnostic, or validated therapeutic intervention protocol.

---

## 2. Transcriptomic Clock Validation & Transfer Limitations

### 2.1 Internal Validation: MAGNet Human Heart Cohort
Model evaluation on human left ventricular tissue profiles from the Myocardial Applied Genomics Network (MAGNet) establishes the following internal benchmarks:
* **Coefficient of Determination ($R^2$):** $0.418$
* **Internal Mean Absolute Error (MAE):** $8.27\text{ years}$

### 2.2 External Validation & Oracle-Assistance Disclosure: GTEx Cohort
External cross-cohort validation was conducted on human left ventricle ($n=432$) and atrial appendage ($n=429$) bulk RNA-seq samples from the Genotype-Tissue Expression (GTEx) project:
* **Direct Transfer MAE (Only Deployable Number):** **$90.05\text{ years}$** (mean predicted age: $-35.69\text{ yr}$, mean offset: $-91.24\text{ yr}$).  
  *Uncalibrated zero-shot transfer fails catastrophically due to technical platform shifts (unaligned sequencing chemistry, library preparation protocols, and post-mortem baseline shifts).*
* **Oracle-Assisted Metrics (NOT Deployable):**
  * **Mean-Calibrated MAE:** $9.51\text{ years}$ in LV (requires subtracting the true mean age of the external cohort—an oracle operation impossible on samples of unknown age).
  * **Within-Cohort Standardized MAE:** $8.69\text{ years}$ in LV (requires knowing the true mean and standard deviation of the external cohort).
  * **Trivial Constant-Mean Donor Baseline MAE:** $8.38\text{ years}$ in LV.
  * **Finding:** When tested externally, the mean-calibrated model ($9.51\text{ yr}$) does not outperform the trivial constant-mean donor baseline ($8.38\text{ yr}$).
* **Atrial Transfer & Baseline Matching:**
  * In the atrial appendage, unrefitted transfer achieved an oracle-calibrated MAE of $7.87\text{ years}$ against a constant-mean baseline of $8.13\text{ years}$.
  * **Statistical Significance:** Paired Wilcoxon $p = 0.467$, paired $t$-test $p = 0.783$. The clock **matches** the constant-mean baseline; it does **not** statistically outperform it.
* **Legitimate Platform Calibration Protocol (Proposed Remediation):**
  * Rather than post-hoc oracle centering, deploying the clock to a new platform requires an empirical reference calibration panel of $24\text{–}32$ known-age biological standards (spanning ages 20–80) processed on the target sequencing chemistry and library protocol.
  * Estimated wet-lab execution cost: $\approx \$8,000\text{–}\$12,000$ ($24\text{–}32$ bulk RNA-seq libraries @ $\$300\text{–}\$400/\text{sample}$).

### 2.3 Model Governance & Architecture Lock
* **Locked Headline Model:** **Model 166** (trained on all $N = 166$ MAGNet non-failing donors with recorded chronological age; $\alpha = 100.0$, 100 features).
  * **Direct Transfer MAE:** $90.05\text{ years}$ ($r = 0.162$, $\rho = 0.165$, mean predicted age: $-35.69\text{ yr}$).
  * **Mean-Calibrated MAE:** $9.51\text{ years}$ (vs $8.38\text{ yr}$ baseline, $R^2 = -0.158$).
  * **Within-Cohort Standardized MAE:** $8.69\text{ years}$ ($r = 0.407$, within-tissue variance normalized).
* **Pre-External Basis:** Designated as the primary model prior to external testing to maximize training sample size ($N = 166$ vs $N = 161$) and avoid discarding donors lacking secondary technical covariates.
* **Secondary Model Disclosure (Reconciled Metrics):** 
  * **Model 161** ($N = 161$ complete-case donors with full clinical covariates; $\alpha = 56.23$):
    * **Direct Transfer MAE:** $56.52\text{ years}$ ($r = 0.379$, $\rho = 0.346$, mean predicted age: $-1.35\text{ yr}$).
    * **Mean-Calibrated MAE:** $8.30\text{ years}$ (vs $8.38\text{ yr}$ baseline, $R^2 = +0.140$).
    * **Within-Cohort Standardized MAE:** $8.79\text{ years}$ ($r = 0.394$).
  * *Note on Earlier Draft Contradiction:* An earlier intermediate summary draft erroneously cited "$9.42\text{ yr} \ (r = 0.222)$" due to a transcription error. The verified, reproducible metrics above are derived directly from the canonical benchmark evaluation in `step2c_gtex_validation_results.json`.
* **Governance Rule:** To prevent post-hoc test-set selection bias (selecting Model 161 after observing superior external calibration), Model 166 remains the formally locked headline model.
* **Lock Date:** 26 September 2026.

### 2.4 Single-Cell Atrial Cohort: PERIHEART Leave-One-Donor-Out (LODO)
On $N = 54$ living surgical donors in the PERIHEART atlas ($88,561$ right atrial appendage cardiomyocytes; decade-binned targets):
* **LODO Ridge Clock MAE:** $6.97\text{ years}$ ($r = 0.4606$, $p = 4.57 \times 10^{-4}$; permutation null MAE $= 9.05 \pm 0.80\text{ yr}$, empirical $p = 0.0030$).
* **Constant-Median Baseline MAE:** $7.59\text{ years}$ (clock improvement $= 0.62\text{ yr}$ / $8.15\%$, paired $t = -0.83$, $p = 0.41$, not statistically significant).
* **Quantization Floor:** $2.50\text{ years}$ due to 10-year age-binning in source donor metadata.
* **Tissue Scope Disclosure:** Evaluated exclusively on right atrial appendage tissue; zero ventricular cardiomyocytes are present in the PERIHEART cohort.

---

## 3. Three-Tier Replicated Aging Biomarker Panel

### 3.1 Biomarker Classification & Scope Boundary (Causality Untested)
The aging signature represents an **age-associated, cross-cohort replicated biomarker panel and candidate assay endpoint**. It does **not** constitute a validated target list or "robust core":
* **No Causal Therapeutic Levers:** No gene in this signature has been shown to causally drive cellular rejuvenation upon knockdown or over-expression.
* **Senescence Readouts:** **`EDA2R`** is a p53-responsive transcriptional target and cellular senescence readout (an **endpoint**, not a therapeutic **lever**).
* **De-Escalation from "Robust Core":** The term "16-gene robust core" is scientifically overbroad: 6 of the 16 genes fail to replicate nominally under manner-of-death control, with `RBM11` losing $95.5\%$ of its effect size ($\beta = +0.00085 \to +0.00004$, $p = 0.964$), `RYR3` losing $42.2\%$ ($\beta = +0.00353 \to +0.00204$, $p = 0.292$), and `ENSG00000184905` losing $40.4\%$ ($p = 0.533$).

### 3.2 Formal Three-Tier Evidence Classification (Hardy-Adjusted Headline)
All external GTEx statistics are cited primarily from the fully-specified, confound-adjusted model (`expression ~ age + sex + SMRIN + SMTSISCH + factor(DTHHRDY)`, $n=431$ non-null donors), with unadjusted values shown secondarily:

1. **Tier 1 — Genome-Wide Replicated ($q < 0.10$, Hardy-Adjusted): 3 Genes**
   * **`EDA2R`:** $\beta_{\text{Hardy}} = \mathbf{+0.01711}, \ p = \mathbf{1.14 \times 10^{-8}}, \ q = \mathbf{6.41 \times 10^{-4}}$ [Simpler unadjusted model: $\beta = +0.01858, p = 1.44 \times 10^{-10}$].
   * **`PTCHD4`:** $\beta_{\text{Hardy}} = \mathbf{+0.00746}, \ p = \mathbf{1.91 \times 10^{-5}}, \ q = \mathbf{0.0895}$ [Simpler unadjusted model: $\beta = +0.00833, p = 8.75 \times 10^{-7}$].
   * **`LINC02388`:** $\beta_{\text{Hardy}} = \mathbf{+0.01265}, \ p = \mathbf{7.12 \times 10^{-6}}, \ q = \mathbf{0.0572}$ [Simpler unadjusted model: $\beta = +0.01130, p = 5.66 \times 10^{-5}$].
2. **Tier 2 — Nominal Chamber Replicated ($p < 0.05$, Hardy-Adjusted): 10 of 16 Genes**
   * `EDA2R` ($p = 1.14 \times 10^{-8}$), `PTCHD4` ($p = 1.91 \times 10^{-5}$), `LINC02388` ($p = 7.12 \times 10^{-6}$), `SPATA18` ($p = 1.74 \times 10^{-3}$), `ELOVL7` ($p = 3.56 \times 10^{-3}$), `VGLL2` ($p = 7.99 \times 10^{-3}$), `CP` ($p = 2.04 \times 10^{-2}$), `ENSG00000244681` ($p = 2.96 \times 10^{-2}$), `FAM118B` ($p = 3.01 \times 10^{-2}$), and `EFNB3` ($p = 3.20 \times 10^{-2}$).
3. **Tier 3 — Directional Concordance: 16 of 16 Genes ($100.0\%$)**
   * All 16 candidate markers preserve identical sign of effect between MAGNet and GTEx under Hardy adjustment (exact binomial $p = \mathbf{1.53 \times 10^{-5}}$).

### 3.3 Cohort Independence & Chamber Structure Disclosure
* **Donor Overlap:** GTEx left ventricle ($n=432$) and atrial appendage ($n=429$) samples originate from **300 shared donors** ($69.4\%$ of LV, $69.9\%$ of AA).
* **Interpretation:** Findings reflect **tissue-level chamber replication within a single donor cohort**, not two independent biological replications. The cross-chamber effect size correlation ($r = 0.644$) is driven in significant part by shared-donor genetic and physiological architecture.

### 3.4 Adults-Only Validation Cohort (Resolution of Pediatric Bias)
GTEx donor enrollment is restricted to adults aged $\ge 20\text{ years}$ (youngest bracket 20–29; zero donors under 20). External replication in GTEx confirms that the age associations of Tier 1 and Tier 2 markers hold strictly in adult human myocardium, resolving prior concerns that discovery associations were driven by pediatric/adolescent donors (ages 15–18).

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
| **11 Jun 2026 – 26 Sep 2026** | Client-Side GRN Telemetry | "Safety Index: 93%" · "✔ Reprogramming Safety Met" | **Fabricated Safety Scores & Guarantees.** Hovering over pioneer transcription factor nodes in `js/script.js` (lines 4957–4961) rendered hardcoded `Safety Index: 93%` and `✔ Reprogramming Safety Met` (e.g. for `NKX2-5` with arbitrary layout weight `safety: 0.93`). Float fixtures were presented to users as empirical safety calculations. | `js/script.js:4957-4961`, `index.html` GRN visualizer | 26 Sep 2026 | **Refuted / Fabricated UI Display (Purged)** |
| **23 Sep 2026** | Platform Traceability | "Traceable to its underlying models" | **Fabricated Outputs.** On 23 Sep 2026, the live platform served hardcoded prescription drug clock shifts, synthetic fallback PDB structures, and uncalibrated clinical trial endpoints. | Production repository audit | 26 Sep 2026 | **Refuted / Stale Deployment** |

