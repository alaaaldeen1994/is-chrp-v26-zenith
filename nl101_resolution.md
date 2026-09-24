# Zenith — Phase B Deliverable: `NL-101` Definition Resolution (`nl101_resolution.md`)

## 1. Canonical `NL-101` Definition

**Canonical Lead Cocktail (`NL-101`):** **`SIRT1 + SIRT6 + GATA4 + ZBTB16`**

- **`SIRT1`** (`ENSG00000096717`): NAD-dependent deacetylase sirtuin-1 (chromatin silencing, FOXO/PGC-1$\alpha$ activation).
- **`SIRT6`** (`ENSG00000077463`): NAD-dependent deacetylase/mono-ADP-ribosyltransferase sirtuin-6 (H3K9ac/H3K56ac deacetylation, LINE-1 silencing, DSB repair).
- **`GATA4`** (`ENSG00000136574`): Cardiac master zinc-finger transcription factor (`MYH7`, `ATP2A2`, `NKX2-5` activator).
- **`ZBTB16`** (`ENSG00000109906` / `PLZF`): BTB/POZ zinc-finger transcriptional repressor.

---

## 2. Complete Attribution of Prior Results by Molecule

Every historical result in the repository has been audited to verify which exact 4-factor set was evaluated:

| Analysis / Script / File | Molecule Evaluated | Exact Computed / Assigned Result | Provenance & Classification |
| :--- | :--- | :--- | :--- |
| **1. Legacy Screening Script**<br>`run_zenith_screening_pipeline.py:108, 213, 293, 483`<br>`zenith_screening_audit.csv:2` | **`SIRT1 + SIRT6 + GATA4 + ZBTB16`** | • With line `293` override: **`-13.00y`** (`youth_score = 0.928`, `Rank #1`)<br>• With line `293` removed, line `108` (`+1.65` bonus) active: **`+15.45y`** (`youth_score = 0.928`, `Rank #1`)<br>• With both line `293` and line `108` removed (ablation in `verification_results.md`): **`+5.85y`** (`youth_score = 0.350`, `Rank #2` behind `OSKM` `+10.90y`) | **Circular / Hardcoded Identity Branch** (`if {"SIRT1", "SIRT6", "GATA4", "ZBTB16"}.issubset(gset): rejuv_multiplier += 1.65`). |
| **2. Unbiased 3-Step Ridge GRN Screen**<br>`scripts/run_part2_real_screen.py:455, 468`<br>`screen_output.csv:676` (`Stage3_Tracked_NL101`) | **`SIRT1 + SIRT6 + GATA4 + ZBTB16`** | • `youth_restoration_pct_excl`: **`-0.0572%`** (`95%` bootstrap CI: `[-0.1173%, +0.0179%]`, Rank **`#211 / 211`** among 4-TF candidates)<br>• `youth_restoration_pct_incl`: **`+0.0157%`**<br>• `empirical_clock_rev_yr_excl`: **`-0.0698y`**<br>• `empirical_clock_rev_yr_incl`: **`-0.1017y`**<br>• `GJA1_shift`: `+0.00933`, `ATP2A2_shift`: `+0.04631` | **Genuine Empirical Computation (`5,307` human vCMs, `22,635` CollecTRI/DoRothEA/TRRUST edges).** Statistical null result (`0%` restoration). Why? In `models/scvi_model_hca/adata.h5ad`, `SIRT6` is detected in only `0.94%` of vCMs (below the `5%` active-regulator threshold) and `SIRT1`/`SIRT6` have small out-degrees in CollecTRI (`18` and `11` edges vs `NFKB1`'s `784` edges). |
| **3. Top Unbiased GRN Quad Winner**<br>`screen_output.csv:524` (`Stage3_Quads`) | **`NFKB1 + MITF + CTCF + HIF1A`** | • `youth_restoration_pct_excl`: **`+6.0693%`** (`95%` bootstrap CI: `[+5.7651%, +6.2486%]`, Rank **`#1 / 211`**)<br>• `youth_restoration_pct_incl`: **`+6.2089%`**<br>• `empirical_clock_rev_yr_excl`: **`+0.1214y`** | **Genuine Empirical Computation.** Driven in part (`R² = 45.79%`) by regulator out-degree (`2,652` combined GRN edges; drops to Rank `#2` behind `NFKB1+MITF+HIF1A+NFIC` after out-degree residualization). |
| **4. Single-TF Row Misquoted as `-0.0085y`**<br>`screen_output.csv:192` (`Stage1_SingleTF`) | **`GTF3A`** *(Single TF, not `NL-101`)* | • `youth_restoration_pct_excl`: **`-0.0317%`**<br>• `empirical_clock_rev_yr_excl`: **`-0.0085y`** | **Audit Transcription Error Corrected.** `zenith_phase0_to_phase4_master_report.md:77` previously misquoted `-0.0085y` (`GTF3A`) and `SIRT6+ZBTB16+GATA4+NKX2-5` in place of `screen_output.csv:676` (`SIRT1+SIRT6+GATA4+ZBTB16`, `-0.0698y`). |

---

## 3. Files Checked & Standardised in Phase B

1. **Executable Code (`bridge_server.py`, `run_zenith_screening_pipeline.py`, `stage4_eval.py`, `scripts/run_part2_real_screen.py`):** Already 100% consistent (`SIRT1 + SIRT6 + GATA4 + ZBTB16`). No changes required.
2. **HTML & Pitch Decks (`index.html`, `zenith_proofs.html`, `scratch/generate_curie_bio_*.py`, `scratch/generate_longevc_deck.py`):** Already 100% consistent (`SIRT1 + SIRT6 + GATA4 + ZBTB16`). No changes required.
3. **Master Audit Report (`zenith_phase0_to_phase4_master_report.md:72–77`):** Corrected `SIRT6+ZBTB16+GATA4+NKX2-5` and `-0.0085y` to **`SIRT1+SIRT6+GATA4+ZBTB16`** and **`-0.0698y` (`excl`) / `-0.1017y` (`incl`)** (`screen_output.csv:676`), with an explicit note explaining the prior transcription error.
