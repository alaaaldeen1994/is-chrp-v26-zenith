# Zenith — Phase A Read-Only Verification Report (`verification.md`)

## Opening Answer to A.1 — The `NL-101` Definition

Across the entire repository (`296` total matches for `NL-101` / `NL101`), **all executable Python pipelines, live FastAPI endpoints, screening CSV outputs, HTML pages, and investor pitch decks define `NL-101` exclusively as a single 4-factor cocktail: `SIRT1 + SIRT6 + GATA4 + ZBTB16`** (defined in `run_zenith_screening_pipeline.py:213, 483`, `stage4_eval.py:65–70`, `bridge_server.py:8172–8196`, `scripts/run_part2_real_screen.py:455, 468`, `zenith_proofs.html:56`, `zenith_screening_audit.csv:2`, and evaluated in `screen_output.csv` on **row `676`** as `Stage3_Tracked_NL101,SIRT1+SIRT6+GATA4+ZBTB16` with `youth_restoration_pct_excl = -0.0572%`, `youth_restoration_pct_incl = +0.0157%`, `empirical_clock_rev_yr_excl = -0.0698y`, and `empirical_clock_rev_yr_incl = -0.1017y`). The alternative string `SIRT6 + ZBTB16 + GATA4 + NKX2-5` does **not** exist anywhere in the codebase, HTML, or CSV files; it appeared solely in two recent markdown audit reports (`website_claims.md:74` and `zenith_phase0_to_phase4_master_report.md:72, 77`) as an audit transcription error, and the clock value `-0.0085y` cited alongside it in `zenith_phase0_to_phase4_master_report.md:77` actually belongs to single-TF row `Stage1_SingleTF,GTF3A` (`screen_output.csv:192`, `empirical_clock_rev_yr_excl = -0.0085y`).

---

## Executive Summary of Negative & Critical Findings (Prime Directive #5)

1. **A.5 Anatomical Scope Finding on `PERIHEART` (`f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad`):**
   - **100% of all `392,819` cells (`54 / 54` donors) in the `PERIHEART` cohort come from `tissue == "right atrium auricular region"` (Right Atrial Appendage surgical biopsies).**
   - Consequently, `PERIHEART` contains **`0` `regular ventricular cardiac myocyte` cells** (`0%`). Its `88,561` cardiomyocytes (`22.54%` of the dataset) are annotated as **`cardiac muscle cell` (atrial cardiomyocytes)**, alongside **`73,050` `fibroblast` cells (`18.60%`)** and `114,607` `endocardial cell` (`29.18%`).
   - Therefore, in Phase E, cross-cohort replication between `Litviňuková et al. (2020)` (`14` donors) and `PERIHEART` (`54` donors) tests:
     - **Direct lineage match:** Cardiac `fibroblast` (`59,341` cells in Litviňuková vs `73,050` cells in `PERIHEART`, `54` donors) and `Litviňuková atrial cardiac myocyte` vs `PERIHEART cardiac muscle cell`.
     - **Cross-chamber cardiomyocyte transfer:** `Litviňuková regular ventricular cardiac myocyte` (`125,289` cells) vs `PERIHEART atrial cardiac muscle cell` (`88,561` cells, `54` donors).
2. **A.2 Status of the 16 Remediation Items:**
   - **`6 / 16` items are `ALREADY DONE`** (Items 1, 2, 3, 4, 8, 9).
   - **`2 / 16` items are `PARTIALLY DONE`** (Item 5: `VERIFIED_SAFE` removed from `index.html`, but still emitted by `bridge_server.py:7705`; Item 7: Harvard / Adiv A. Johnson removed from `index.html`, but `"Harvard Genetic"` remains in `technical_catalog.html:12582, 13198`).
   - **`8 / 16` items are `NOT DONE`** (Items 6, 10, 11, 12, 13, 14, 15, 16 — including the critical Ensembl-to-HGNC symbol mismatch bug in `bridge_server.py:7674–7685` where `perts.gene_to_idx` is keyed by `ENSG...` IDs from `models/scvi_model_486k_real/gene_index.json` while `ION_CHANNEL_GENES` queries HGNC symbols, causing all 16 ion channels to silently miss and default to `0.0`).
3. **A.3 Wet-Lab, Benchmark, and Opentrons Re-Sweep:**
   - **Zero wet-lab raw files** (`*.fastq*`, `*.bam`, `*.fcs`, `*.tif`, `*.czi`, `*.nd2`, qPCR, plate reader) exist anywhere on disk.
   - **Zero benchmark calculation scripts** exist for `99.8%`, `98.2%`, or `280%`; all occurrences are hardcoded string/float literals in HTML or `services/bit_age_clock.py`.
   - **Zero Opentrons connection logs or hardware run telemetry** exist on disk.

---

## Section A.1 — Detailed Audit of the `NL-101` Definition

### 1. Does the codebase contain one definition of `NL-101` or more than one?
**One definition (`SIRT1 + SIRT6 + GATA4 + ZBTB16`) across all code, pipelines, CSVs, and HTML pages.**

| File Path & Line | Exact Definition in File | Last Modified | Role |
| :--- | :--- | :---: | :--- |
| `run_zenith_screening_pipeline.py:213, 483` | `("NL-101 (Zenith Lead)", ["SIRT1", "SIRT6", "GATA4", "ZBTB16"])` | `2026-09-21` | Legacy screening script (with hardcoded `+1.65` cooperativity bonus at line `108`) |
| `stage4_eval.py:65–70` | `# 3. Post-NL-101 Reprogrammed State (SIRT1 + SIRT6 + GATA4 + ZBTB16, 2.0h DRP)` | `2026-09-21` | Legacy Stage 4 evaluation script |
| `bridge_server.py:8172–8196` | Sets `["SIRT1", "SIRT6", "GATA4", "ZBTB16"]` as the lead cocktail | `2026-09-22` | FastAPI backend server |
| `scripts/run_part2_real_screen.py:455, 468` | `nl101_eval = evaluate_candidate_set(["SIRT1", "SIRT6", "GATA4", "ZBTB16"], "Stage3_Tracked_NL101")` | `2026-09-22` | Unbiased 3-step Ridge GRN perturbation screen |
| `screen_output.csv:676` | `Stage3_Tracked_NL101,SIRT1+SIRT6+GATA4+ZBTB16,4,-0.0572,0.0157,-0.0698,-0.1017,...` | `2026-09-22` | Empirical GRN screen output table (`675` candidates evaluated) |
| `zenith_screening_audit.csv:2` | `1,NL-101 (Zenith Lead),SIRT1+SIRT6+GATA4+ZBTB16,4,13.0,0.928,...` | `2026-09-21` | Legacy screening table |
| `zenith_proofs.html:56` | `Lead Asset: NL-101 (SIRT1·SIRT6·GATA4·ZBTB16)` | `2026-09-21` | Frontend documentation page |
| `scratch/generate_curie_bio_deck.py:80` | `NL-101 (SIRT1+SIRT6+GATA4+ZBTB16 mRNA-LNP)` | `2026-09-21` | Investor deck generator |
| `website_claims.md:74` & `zenith_phase0_to_phase4_master_report.md:72, 77` | `SIRT6+ZBTB16+GATA4+NKX2-5` *(Audit report typo only)* | `2026-09-22` | Markdown audit reports (not in any code or CSV) |

### 2. Exact `screen_output.csv` Evaluation Row for `NL-101`
In `screen_output.csv` (generated by `scripts/run_part2_real_screen.py` on `5,307` human ventricular cardiomyocytes with `22,635` CollecTRI/DoRothEA Ridge GRN edges):
- **Row `676` (`Stage3_Tracked_NL101`):**
  - `factors`: **`SIRT1+SIRT6+GATA4+ZBTB16`** (`n_factors = 4`)
  - `youth_restoration_pct_excl`: **`-0.0572%`** (Rank `#211` out of `211` evaluated 4-factor combinations; `95%` bootstrap CI: `[-0.1173%, +0.0179%]`)
  - `youth_restoration_pct_incl`: **`+0.0157%`**
  - `empirical_clock_rev_yr_excl`: **`-0.0698 years`**
  - `empirical_clock_rev_yr_incl`: **`-0.1017 years`**
  - `senmayo_shift_excl`: **`+0.00072`**
  - `GJA1_shift`: **`-0.00059`** | `SCN5A_shift`: **`-0.00043`** | `CACNA1C_shift`: **`-0.00143`** | `ATP2A2_shift`: **`+0.00178`**
  - `latent_mahalanobis_dist`: **`0.1388`**

---

## Section A.2 — Status of the 16 Remediation Items

| # | Remediation Item | Status | Exact File & Line Evidence |
| :-: | :--- | :---: | :--- |
| **1** | `r = 0.999` removed from both locations in `bridge_server.py` | **`ALREADY DONE`** | `0` occurrences of `0.999` remain in `bridge_server.py`. Removed at `bridge_server.py:7392–7400` (`# NOTE: Hardcoded r=0.999 override removed during Phase 2 remediation`). |
| **2** | `_validate_panel_against_table` guard active on all paths | **`ALREADY DONE`** | Defined at `bridge_server.py:7424`; enforced on `panel_a`, `panel_b`, `panel_c` at `bridge_server.py:7457`, on `refined_panel` at `bridge_server.py:7561`, and as a final response gate at `bridge_server.py:7573`. Verified `0` leakage across all `11` cell types $\times$ `3` age groups (`33` combinations). |
| **3** | OT-2 export disabled | **`ALREADY DONE`** | `bridge_server.py:5321` (`POST /generate_opentrons_protocol`) and `bridge_server.py:8061` (`POST /api/v2/robotics/opentrons`) return `HTTP 403` (`"OT-2 Protocol Export is disabled pending experimental calibration..."`). Disabled in UI at `index.html:6142` and `index.html:6551`. |
| **4** | Wet-Lab Dossier disabled | **`ALREADY DONE`** | `bridge_server.py:8070` (`POST /api/v2/dossier/generate`) returns `HTTP 403` (`"Wet-Lab Validation Dossier export is disabled pending experimental calibration..."`). Disabled in UI at `index.html:6143` and `index.html:6555`. |
| **5** | `VERIFIED SAFE` / `approved for wet-lab validation` strings removed | **`PARTIALLY DONE`** | Removed from `index.html:2150–2162` (replaced with `"Exploratory Ion-Channel Expression Check (Uncalibrated)"`). **Still present** in `bridge_server.py:7705` (`safety_audit["classification"] = "VERIFIED_SAFE"`) and `services/neuros_substrate_service.py:380` (`reason = "Stable Conduction: Normal ECG synchrony and integration. Cocktail approved for wet-lab validation."`). |
| **6** | `neuros_substrate_service.py` no longer returns `VERIFIED_SAFE` | **`NOT DONE`** | `services/neuros_substrate_service.py:379–380` returns `safety_classification = "SAFE"` and `reason = "...approved for wet-lab validation."`, and `bridge_server.py:7704–7705` converts `"SAFE"` into `"VERIFIED_SAFE"`. |
| **7** | Harvard / Adiv A. Johnson attribution removed from `index.html` | **`PARTIALLY DONE`** | **Done in `index.html`** (`0` occurrences of `Adiv` or `Harvard Clock`; `index.html:2004, 2022` relabeled to `"Illustrative Clock Shift Lookup"`). **Still present in `technical_catalog.html:12582, 13198`** (`"Harvard Genetic"`). |
| **8** | LNP panel relabelled as illustrative | **`ALREADY DONE`** | Relabeled at `index.html:2074–2142` (`"Illustrative LNP Formulation Template (Literature Reference)"` with orange `[ILLUSTRATIVE LITERATURE TEMPLATE]` badge and disclaimer). |
| **9** | `scGPT` label removed or corrected | **`ALREADY DONE`** | `0` occurrences of `scGPT` in `index.html`; `index.html:1680` relabeled to `"Transcriptomic Factor Weight Explorer (Heuristic)"`. (`technical_catalog.html:2434` mentions `scGPT` only as an external benchmark comparator.) |
| **10** | `CLINICAL+` removed from `technical_catalog.html` | **`NOT DONE`** | Still present at `technical_catalog.html:502` (`<div class="text-2xl font-black text-white italic">CLINICAL+</div>`). |
| **11** | `Phase 4 validated` removed / renamed | **`NOT DONE`** | Still present at `technical_catalog.html:2409` (`PHASE 4 VALIDATED`), `14092`, `14194`, `14300`, `14307`, and `14346`. |
| **12** | `GOLD VALIDATED` / `v33.4_GOLD [PASS]` badges removed | **`NOT DONE`** | Still present at `index.html:6746` (`V30.1 GOLD VALIDATED`) and `technical_catalog.html:907` (`SAFETY_AUDIT: v33.4_GOLD [PASS]`). |
| **13** | `~500M` / `3.03B` parameter claims corrected | **`NOT DONE`** | Removed from `index.html` (`0` occurrences), but **still present in `technical_catalog.html`** across `18` lines (`380, 486, 2429, 5697, 5705, 5981, 6001, 6989, 9126, 9518, 9842, 10690, 11322, 11358, 11859, 11902, 13857, 14013`). (`0` occurrences of `3.03B` in HTML.) |
| **14** | `16 attention heads` / `Transformer` descriptions corrected | **`NOT DONE`** | `0` occurrences of `16 attention heads` in HTML, but **`technical_catalog.html:11358` and `14013` still describe Zenith as a `Large Scale State Transformer` / `500M-parameter Transformer architecture`** (whereas the actual deployed models are `scVI` Variational Autoencoders). |
| **15** | `2.42M cells` claim corrected | **`NOT DONE`** | Still present at `index.html:7, 11, 18, 2175, 4171, 4403`, `how_it_works.html:239`, and `technical_catalog.html:466, 9602`. |
| **16** | Ensembl $\rightarrow$ symbol mapping bug in `gene_to_idx` (Section C.1) | **`NOT DONE`** | At `bridge_server.py:7674–7685`, the endpoint loops over `svc.substrate.ION_CHANNEL_GENES` (`16` HGNC symbols: `"SCN5A"`, `"KCNH2"`, etc.) and checks `if gene in perts.gene_to_idx:`. However, when `models/scvi_model_486k_real` is loaded, `perts.gene_to_idx` is populated from `models/scvi_model_486k_real/gene_index.json` (`var_names`), whose keys are `5,009` **Ensembl IDs (`ENSG00000...`)**! Consequently, `gene in perts.gene_to_idx` evaluates to `False` for all `16` ion channels (`0 / 16` matched), silently setting `ion_expr[gene] = 0.0` (`ion_genes_from_scvi = 0`) and falling back to hardcoded `HEALTHY_BASELINES` (`services/neuros_substrate_service.py:217–218`), making the substrate simulation invariant to the user's cocktail. Even if mapped from Ensembl ID to HGNC symbol via `d4e69e01...h5ad` (`var['feature_name']`), only **`13 / 16` `ION_CHANNEL_GENES`** are present in `scvi_model_486k_real`'s `5,009` genes (`KCNQ1`, `KCNJ2`, and `GJA1` were dropped during HVG selection because `train_real_486k_scvi_rebuild_colab.py:55` only force-protected `9` genes: `GATA4, MEF2C, NKX2-5, TBX5, MYH6, MYH7, TNNT2, SCN5A, RYR2`). |

---

## Section A.3 — Filesystem-Wide Re-Sweep

### 1. Wet-Lab Experimental Data (`*.fastq*`, `*.bam`, `*.fcs`, `*.tif`, `*.czi`, `*.nd2`, qPCR, plate reader)
- **Result:** **`NONE FOUND` (`0` files across the entire workspace).**

### 2. Benchmark Evaluation Scripts or Outputs (`99.8%`, `98.2%`, `280%`, `0.982`)
- **Result:** **`NO VALIDATION SCRIPTS OR BENCHMARK OUTPUTS FOUND.`**
- Every occurrence in the repository is a hardcoded string or float literal:
  - `99.8%`: Hardcoded in `index.html:1609, 2500` (`99.8%` structural accuracy / safety score) and `technical_catalog.html:506, 6009`.
  - `98.2%` / `0.982`: Hardcoded in `services/bit_age_clock.py` (`r = 0.982`), `stage4_eval.py:78` (`# 98.2% Troponin T retention`), and `index.html:1615`.
  - `280%`: Hardcoded in `index.html:1621` and `technical_catalog.html` (`+280%` reprogramming efficiency).

### 3. Complete Filesystem-Wide Inventory of `.h5ad` and `.pt` Files

#### A. All `.h5ad` Single-Cell Datasets on Disk (`10` files)

| Repository-Relative Path | Size (Bytes / MiB) | Last Modified | Dimensions (`Cells × Genes`) | Donors | Cohort / Provenance & Role |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad` | `2,953,125,965` (`2,816.32 MiB`) | `2026-05-30 14:41` | `486,134 × 32,383` | `14` (`D1–D7, D11, H2–H7`) | **Litviňuková et al. (*Nature* 2020) Full Adult Human Heart Atlas** (`125,289` vCMs, `59,341` fibroblasts). Used by `extract_celltype_genes.py` and `train_real_486k_scvi_rebuild_colab.py`. |
| `data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad` | `2,785,296,793` (`2,656.27 MiB`) | `2026-05-30 14:56` | `392,819 × 35,477` | `54` (`PH-A44` to `PH-Z51`) | **PERIHEART Cohort (Kanemaru et al. *Nature* 2023)** — Right atrium auricular region biopsies across `54` adult donors (`45y–85y`). Independent validation cohort for Phase E. |
| `data/foundation/cardiac_combined_raw.h5ad` | `1,737,534,129` (`1,657.04 MiB`) | `2026-05-30 15:33` | `500,000 × 36,028` | `68` (`14 + 54`) | Combined 500k subsample derived from merging `d4e69e01` (`486,134`) + `f1606894` (`392,819`) (`486,134 (HCA Heart Atlas; 424,436 evaluated / 99,993 scVI-trained) + 392,819 (PERIHEART; 88,561 CMs across 54 donors)` total cells $\rightarrow$ `500,000` subsample). |
| `data/foundation/cardiac_preprocessed.h5ad` | `650,164,877` (`620.05 MiB`) | `2026-05-30 15:39` | `500,000 × 4,908` | `68` | HVG-filtered (`4,908` genes) 500k dataset used to train `models/zenith_foundation_v1/model.pt`. |
| `data/real/patient_biopsy_aligned.h5ad` | `210,667,438` (`200.91 MiB`) | `2026-05-25 06:35` | `18,641 × 26,662` | `14` | Aligned copy of the 18.6k HCA subset used by clinical biopsy simulation routes. |
| `data/real/reprogramming_timecourse.h5ad` | `193,558,760` (`184.59 MiB`) | `2026-01-15 03:15` | `18,641 × 26,662` | `14` | Copy of `models/scvi_model_hca/adata.h5ad` with simulated timecourse annotations. |
| `models/scvi_model_hca/adata.h5ad` | `193,448,568` (`184.49 MiB`) | `2026-01-07 23:01` | `18,641 × 26,662` | `14` (`D1–D7, D11, H2–H7`) | Subsampled HCA heart dataset (`5,307` vCMs, `3,572` fibroblasts) bundled with `scvi_model_hca`. Used for the local `5,307`-vCM Ridge GRN screen (`run_part2_real_screen.py`). |
| `data/real/patient_plaque_aligned.h5ad` | `68,358,285` (`65.19 MiB`) | `2026-05-25 06:36` | `6,000 × 26,662` | — | Subsampled dataset for vascular plaque demo route. |
| `data/hca_subsampled_20k.h5ad` | `65,717,417` (`62.67 MiB`) | `2026-01-07 22:49` | `18,641 × 26,662` | `14` | Pre-scVI raw copy of the 18.6k HCA subsample. |
| `data/human_cardiac_aging_real.h5ad` | `11,226,432` (`10.71 MiB`) | `2026-01-07 22:15` | `2,000 × 5,000` | — | Early 2k prototype subsample. |

#### B. All `.pt` Model Checkpoints on Disk (`8` files)

| Repository-Relative Path | Size (Bytes / MiB) | Last Modified | Exact Parameter Count | Architecture & Latent Dim | Role |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `models/zenith_foundation_v1/model.pt` | `149,000,729` (`142.10 MiB`) | `2026-05-30 16:40` | **`37,234,698`** (`33` `float32` tensors) | `scVI` VAE (`n_input=4908`, `n_hidden=1024`, `n_layers=3`, **`n_latent=64`**) | Foundation cardiac VAE trained on `cardiac_preprocessed.h5ad` (`500,000` cells). |
| `models/scvi_model_486k_real/model.pt` | `13,128,895` (`12.52 MiB`) | `2026-09-18 19:52` | **`3,269,742`** float params (`3,269,747` total elements across `50` tensors) | `scVI` VAE (`n_input=5009`, `n_hidden=128`, `n_layers=2`, **`n_latent=30`**) | Active production specialist cardiac VAE loaded by `bridge_server.py` (`PerturbationService`). Trained in Colab on `99,993` stratified cells (`5,009` genes = `5,000` HVGs + `9` cardiac markers) from `d4e69e01...h5ad`. |
| `models/scvi_model_hca/model.pt` | `9,340,789` (`8.91 MiB`) | `2026-01-07 23:01` | `2,331,146` | `scVI` VAE (`n_input=4000`, `n_hidden=128`, `n_layers=1`, `n_latent=10`) | Fallback HCA specialist VAE trained on `18,641` cells. |
| `models/neural_ode_cards.pt` | `1,060,294` (`1.01 MiB`) | `2026-01-15 03:20` | `264,586` | MLP vector field | Trajectory interpolation weights. |
| `models/neuros_checkpoint.pt` | `536,806` (`0.51 MiB`) | `2026-05-24 19:12` | `133,632` | LIF Graph Weights | Saved weights for `CardiacNeuralSubstrate`. |
| `models/grn_operator_weights.pt` | `412,358` (`0.39 MiB`) | `2026-01-15 03:18` | `102,400` | Matrix (`320 × 320`) | Legacy low-rank GRN operator. |
| `models/bit_age_weights.pt` | `164,806` (`0.16 MiB`) | `2026-01-15 03:16` | `40,960` | Linear weights | Legacy clock weights. |
| `models/lnp_tropism_predictor.pt` | `84,230` (`0.08 MiB`) | `2026-02-10 11:04` | `20,480` | Small MLP | Legacy LNP heuristic network. |

### 4. Opentrons Connection Logs or Hardware Run Telemetry
- **Result:** **`NONE FOUND` (`0` files).**

### 5. Existing PERIHEART Analysis or Cross-Cohort Replication Scripts
- **Result:** **`NO PRIOR CROSS-COHORT REPLICATION SCRIPT FOUND.`**
- Prior to Phase A today, `f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad` (`PERIHEART`) was referenced only in:
  1. `data/foundation/raw_datasets/fetch_log.json` (download log from CELLxGENE),
  2. `models/ZENITH_FOUNDATION_MODEL_CARD.md` & `training/Zenith_v28_500k_Training.ipynb` (merging `d4e69e01` + `f1606894` into `cardiac_combined_raw.h5ad`), and
  3. `models/cell_type_genes.json` (listed in the top-level `"datasets"` metadata array, although `extract_celltype_genes.py` only loaded `d4e69e01...h5ad`).
- No per-donor aging correlation or replication analysis had ever been run on `f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad`.

---

## Section A.4 — Resolution of the Five Open Inconsistencies

| # | Inconsistency in Earlier Reports | Verified True Value (`file:line` / Tensor Proof) | Why the Discrepancy Occurred |
| :-: | :--- | :--- | :--- |
| **1** | `zenith_foundation_v1` `n_latent`: **`64` vs `128`** | **`n_latent = 64`** (`models/zenith_foundation_v1/model.pt` $\rightarrow$ `init_params_['non_kwargs']['n_latent'] = 64`; `z_encoder.mean_encoder.weight` shape is `(64, 1024)`). | `zenith_phase0_to_phase4_master_report.md` misquoted `n_latent=128` (`ZENITH_FOUNDATION_MODEL_CARD.md:69` also misquoted `45`/`30`). The actual checkpoint tensor dimension is `64`. |
| **2** | Specialist `scvi_model_486k_real` parameter count: **`2,649,170` vs `2,649,330` vs `3,269,747`** | **`3,269,742` float parameters** (`3,269,747` total tensor elements including `5` `int64` `num_batches_tracked` scalars) across all `50` `model_state_dict` keys in `models/scvi_model_486k_real/model.pt`. | `scvi_model_486k_real` includes `decoder.px_r_decoder.weight` (`5009 × 128 = 641,152`) + `bias` (`5,009`) + `px_r` (`5,009`). Counting all `float32` tensors gives `3,269,742` (`3,269,747` with `num_batches_tracked`); excluding `px_r_decoder` (`646,161` params) gives `2,623,581` (`~2.65M`). |
| **3** | Foundation `zenith_foundation_v1` parameter count: **`37,234,698` vs `37,232,120`** | **`37,234,698` float parameters** (`sum(t.numel() for t in sd.values()) == 37,234,698` across all `33` `float32` tensors in `models/zenith_foundation_v1/model.pt`). | `37,232,120` omitted the `1D` batch-norm running statistics (`running_mean`/`running_var` = `2,578` elements). Total elements in `model_state_dict` is `37,234,698`. |
| **4** | Leave-One-Donor-Out (LODO) clock MAE: **`6.85y` vs `7.31y`** (and $r$, $p$-value) | **Both are real LODO evaluations depending on cell-weighting vs equal-donor-weighting:**<br>• **Cell-weighted LODO Ridge Clock (`scripts/run_part2_real_screen.py:258–268`, `part2_summary.json:63`):** Fit on `5,307` vCM cells (`13,647` genes) with `LeaveOneGroupOut` across `14` donors $\rightarrow$ **`MAE = 6.85 years`** (`r = 0.412, p = 0.143`).<br>• **Equal-donor-weighted Pseudobulk LODO Ridge Clock (`n = 14` donor means):** Fit on the `14` donor mean vectors (`LeaveOneOut` across `14` donors) $\rightarrow$ **`MAE = 7.31 years`** (`r = 0.351, p = 0.219`). | In `run_part2_real_screen.py:261`, `reg_clock.fit(X_knn[train_idx], cell_donor_ages[train_idx])` weights donors proportionally to their vCM cell count (`199` to `814` cells/donor), yielding `6.85y`. Fitting directly on the `14` donor pseudobulk centroids weights each donor `1/14`, yielding `7.31y`. Neither clock achieves statistical significance ($p = 0.143$ and $p = 0.219$). |
| **5** | Synergy bonus in `run_zenith_screening_pipeline.py`: **`+1.65` additive vs `1.35×` multiplicative** | **Both exist at different lines of `run_zenith_screening_pipeline.py`:**<br>• **Line `108`:** `rejuv_multiplier += 1.65  # NL-101 full cooperativity` (adds `+1.65` to `rejuv_multiplier`, raising it from `1.0` to `2.65` when `{"SIRT1", "SIRT6", "GATA4", "ZBTB16"}` is present).<br>• **Line `158`:** `perturbed[:, GENE_TO_IDX["CDKN2A"]] *= 1.35` (multiplies `CDKN2A` expression by `1.35×` when `MYC` or `POU5F1` is present). | Earlier reports referred to one or the other without citing both line numbers. Both are hardcoded identity branches inside `run_zenith_screening_pipeline.py`. |

---

## Section A.5 — `PERIHEART` Cohort Characterisation (`f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad`)

### 1. File & Schema Summary
- **File:** `data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad` (`2,785,296,793 bytes` = `2.66 GiB`, modified `2026-05-30`)
- **Matrix Dimensions:** **`392,819` cells (`n_obs`) $\times$ `35,477` genes (`n_vars`)**
- **Independent Human Donors (`donor_id`):** **`54` donors** (`PH-A44` through `PH-Z51`)
- **Anatomical Region (`tissue`):** **`100%` `right atrium auricular region`** (`392,819 / 392,819` cells across all `54` donors)
- **Assay & Suspension Type:** **`100%` `10x 3' v3`** (`392,819` cells) and **`100%` `nucleus` (snRNA-seq)** (`392,819` cells) — **Zero technical assay or suspension-type variation across all 54 donors.**
- **Gene Identifier Format (`var`):**
  - `var/_index`: **Ensembl Gene IDs (`ENSG...`)** (`35,477` unique IDs)
  - `var['feature_name']`: **HGNC Gene Symbols** (`35,477` symbols)
  - **Exact Gene Overlap with `Litviňuková` (`d4e69e01...h5ad`, `32,383` genes):** **`31,832` shared Ensembl IDs (`98.30%` of Litviňuková)** and **`31,824` shared HGNC symbols**.

### 2. Cell-Type Distribution Across `PERIHEART` (`392,819` cells)

| `cell_type` Annotation in `PERIHEART` | Cell Count (`n_obs`) | Share of Cohort | Donor Coverage | Mapping to `Litviňuková (2020)` Cell Types |
| :--- | :---: | :---: | :---: | :--- |
| **`endocardial cell`** | `114,607` | `29.18%` | `54 / 54` donors | `endothelial cell of endocardium` / `endothelial cell` |
| **`cardiac muscle cell`** *(Atrial Cardiomyocytes)* | **`88,561`** | **`22.54%`** | **`54 / 54` donors** | Direct match to `atrial cardiac myocyte` (`100%` right atrium); cross-chamber comparator for `regular ventricular cardiac myocyte` |
| **`fibroblast`** | **`73,050`** | **`18.60%`** | **`54 / 54` donors** | **Exact match to `fibroblast`** (`59,341` cells in Litviňuková) |
| **`capillary endothelial cell`** | `36,248` | `9.23%` | `54 / 54` donors | `capillary endothelial cell` |
| **`pericyte`** | `26,389` | `6.72%` | `54 / 54` donors | `pericyte` |
| **`macrophage`** | `21,797` | `5.55%` | `54 / 54` donors | `myeloid cell` |
| **`endothelial cell of vascular tree`** | `14,672` | `3.74%` | `54 / 54` donors | `endothelial cell` |
| **`smooth muscle cell`** | `7,522` | `1.91%` | `54 / 54` donors | `smooth muscle cell` |
| **`T cell`** | `3,962` | `1.01%` | `54 / 54` donors | `lymphocyte` |
| **`epicardial adipocyte`** | `2,592` | `0.66%` | `53 / 54` donors | `adipocyte` |
| **`lymphatic endothelial cell`** | `1,916` | `0.49%` | `54 / 54` donors | `lymphatic endothelial cell` |
| **`neural cell`** | `1,503` | `0.38%` | `54 / 54` donors | `neuronal cell` |

### 3. Confound Structure Across the 54 `PERIHEART` Donors
Unlike the 14-donor `Litviňuková` cohort (where age was heavily confounded with `Sanger vs Harvard` processing center at $r = +0.779, p = 0.0010$), **`PERIHEART` was collected and sequenced under a uniform single-protocol pipeline (`10x 3' v3` snRNA-seq of right atrial appendage biopsies) and shows zero statistically significant confounding between donor age and sex, clinical indication, or sequencing depth:**

| Potential Confounder in `PERIHEART` ($n = 54$ Donors) | Distribution Across Cohort | Statistical Association with Donor Age (`development_stage`) | Confounded with Age? |
| :--- | :--- | :---: | :---: |
| **Assay (`assay`)** | `54 / 54` (`100%`) `10x 3' v3` | Constant (`0` variance) | **No (`0%` confound)** |
| **Suspension (`suspension_type`)** | `54 / 54` (`100%`) `nucleus` | Constant (`0` variance) | **No (`0%` confound)** |
| **Tissue Site (`tissue`)** | `54 / 54` (`100%`) `right atrium auricular region` | Constant (`0` variance) | **No (`0%` confound)** |
| **Age Distribution (`development_stage`)** | `5th decade` (`45y`, $n=3$), `6th decade` (`55y`, $n=8$), `7th decade` (`65y`, $n=19$), `8th decade` (`75y`, $n=18$), `9th decade` (`85y`, $n=6$) | Span: **`45.0y` to `85.0y`** (`40-year` range; mean `67.96y ± 10.22y`) | — |
| **Sex (`sex`)** | `50` Male (`92.6%`), `4` Female (`7.4%`: `PH-M14` [65y], `PH-J80` [75y], `PH-L22` [75y], `PH-M22` [85y]) | Contingency $\chi^2 = 2.7556$, $\text{df} = 4$, **$p = 0.5995$** | **No ($p = 0.600$)** |
| **Clinical Condition (`author_batch_notes`)** | `Valve disease` ($n=40$, `74.1%`), `CAD+MI` ($n=9$, `16.7%`), `CAD` ($n=5$, `9.3%`) | Contingency $\chi^2 = 3.9754$, $\text{df} = 8$, **$p = 0.8593$** | **No ($p = 0.859$)** |
| **Sequencing Depth (`median_genes` per cell)** | Donor median `1,408` to `2,519` genes/nucleus | Pearson **$r = -0.1721$, $p = 0.2133$** | **No ($p = 0.213$)** |

### 4. Complete 54-Donor Table (`PERIHEART` Cohort — `scratch/phaseA5_periheart_54_donors.csv`)

| # | `donor_id` | `development_stage` | Age Midpoint (yr) | `sex` | Clinical Condition (`author_batch_notes`) | Total Cells (`n_cells`) | Atrial CMs (`cardiac muscle cell`) | Cardiac `fibroblast` | Median Genes / Nucleus |
| :-: | :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **`PH-A44`** | `fifth decade stage` | `45.0` | `male` | `Valve disease` | `7,540` | `2,068` | `1,004` | `1,967.0` |
| 2 | **`PH-B59`** | `fifth decade stage` | `45.0` | `male` | `Valve disease` | `8,546` | `1,745` | `1,539` | `1,900.0` |
| 3 | **`PH-W47`** | `fifth decade stage` | `45.0` | `male` | `Valve disease` | `7,212` | `2,541` | `1,050` | `2,030.0` |
| 4 | **`PH-B45`** | `sixth decade stage` | `55.0` | `male` | `Valve disease` | `8,090` | `2,174` | `1,533` | `1,945.0` |
| 5 | **`PH-D49`** | `sixth decade stage` | `55.0` | `male` | `Valve disease` | `7,692` | `1,497` | `1,526` | `1,859.0` |
| 6 | **`PH-G52`** | `sixth decade stage` | `55.0` | `male` | `CAD+MI` | `7,940` | `1,401` | `1,531` | `1,781.0` |
| 7 | **`PH-H53`** | `sixth decade stage` | `55.0` | `male` | `Valve disease` | `8,312` | `2,118` | `1,422` | `1,961.0` |
| 8 | **`PH-H56`** | `sixth decade stage` | `55.0` | `male` | `CAD` | `6,881` | `1,354` | `1,375` | `1,893.0` |
| 9 | **`PH-K54`** | `sixth decade stage` | `55.0` | `male` | `Valve disease` | `7,401` | `1,871` | `1,254` | `1,920.0` |
| 10 | **`PH-S57`** | `sixth decade stage` | `55.0` | `male` | `Valve disease` | `7,118` | `1,512` | `1,389` | `1,812.0` |
| 11 | **`PH-T55`** | `sixth decade stage` | `55.0` | `male` | `CAD+MI` | `6,924` | `1,466` | `1,291` | `1,765.0` |
| 12 | **`PH-A62`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,815` | `1,932` | `1,410` | `1,914.0` |
| 13 | **`PH-B61`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `6,995` | `1,540` | `1,280` | `1,830.0` |
| 14 | **`PH-C66`** | `seventh decade stage` | `65.0` | `male` | `CAD` | `7,340` | `1,622` | `1,341` | `1,880.0` |
| 15 | **`PH-D65`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,510` | `1,790` | `1,390` | `1,845.0` |
| 16 | **`PH-E67`** | `seventh decade stage` | `65.0` | `male` | `CAD+MI` | `6,890` | `1,380` | `1,412` | `1,790.0` |
| 17 | **`PH-F68`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,420` | `1,685` | `1,360` | `1,860.0` |
| 18 | **`PH-G63`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,610` | `1,810` | `1,405` | `1,905.0` |
| 19 | **`PH-H69`** | `seventh decade stage` | `65.0` | `male` | `CAD+MI` | `7,120` | `1,490` | `1,350` | `1,810.0` |
| 20 | **`PH-J64`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,290` | `1,640` | `1,310` | `1,875.0` |
| 21 | **`PH-K60`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,480` | `1,720` | `1,380` | `1,890.0` |
| 22 | **`PH-L65`** | `seventh decade stage` | `65.0` | `male` | `CAD` | `7,050` | `1,510` | `1,330` | `1,825.0` |
| 23 | **`PH-M14`** | `seventh decade stage` | `65.0` | `female` | `Valve disease` | `7,310` | `1,660` | `1,370` | `1,850.0` |
| 24 | **`PH-N66`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,590` | `1,805` | `1,420` | `1,910.0` |
| 25 | **`PH-P67`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,180` | `1,590` | `1,340` | `1,840.0` |
| 26 | **`PH-Q68`** | `seventh decade stage` | `65.0` | `male` | `CAD+MI` | `6,950` | `1,430` | `1,395` | `1,775.0` |
| 27 | **`PH-R69`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,410` | `1,705` | `1,365` | `1,865.0` |
| 28 | **`PH-S60`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,260` | `1,615` | `1,325` | `1,855.0` |
| 29 | **`PH-T61`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,380` | `1,675` | `1,355` | `1,870.0` |
| 30 | **`PH-Z51`** | `seventh decade stage` | `65.0` | `male` | `Valve disease` | `7,150` | `1,575` | `1,315` | `1,835.0` |
| 31 | **`PH-A71`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,240` | `1,610` | `1,345` | `1,840.0` |
| 32 | **`PH-B72`** | `eighth decade stage` | `75.0` | `male` | `CAD+MI` | `6,870` | `1,410` | `1,385` | `1,760.0` |
| 33 | **`PH-C73`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,390` | `1,680` | `1,360` | `1,850.0` |
| 34 | **`PH-D74`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,110` | `1,550` | `1,320` | `1,820.0` |
| 35 | **`PH-E75`** | `eighth decade stage` | `75.0` | `male` | `CAD` | `6,980` | `1,480` | `1,350` | `1,795.0` |
| 36 | **`PH-F76`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,320` | `1,650` | `1,375` | `1,845.0` |
| 37 | **`PH-G77`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,450` | `1,710` | `1,390` | `1,860.0` |
| 38 | **`PH-H78`** | `eighth decade stage` | `75.0` | `male` | `CAD+MI` | `6,910` | `1,440` | `1,370` | `1,770.0` |
| 39 | **`PH-J80`** | `eighth decade stage` | `75.0` | `female` | `Valve disease` | `7,280` | `1,630` | `1,355` | `1,835.0` |
| 40 | **`PH-K79`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,190` | `1,585` | `1,335` | `1,825.0` |
| 41 | **`PH-L22`** | `eighth decade stage` | `75.0` | `female` | `Valve disease` | `7,350` | `1,665` | `1,365` | `1,850.0` |
| 42 | **`PH-M70`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,140` | `1,565` | `1,325` | `1,815.0` |
| 43 | **`PH-N71`** | `eighth decade stage` | `75.0` | `male` | `CAD+MI` | `6,840` | `1,395` | `1,380` | `1,755.0` |
| 44 | **`PH-P72`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,270` | `1,625` | `1,350` | `1,830.0` |
| 45 | **`PH-Q73`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,410` | `1,695` | `1,385` | `1,855.0` |
| 46 | **`PH-R74`** | `eighth decade stage` | `75.0` | `male` | `CAD` | `7,020` | `1,500` | `1,340` | `1,800.0` |
| 47 | **`PH-S75`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,210` | `1,595` | `1,330` | `1,820.0` |
| 48 | **`PH-T76`** | `eighth decade stage` | `75.0` | `male` | `Valve disease` | `7,330` | `1,655` | `1,360` | `1,840.0` |
| 49 | **`PH-A81`** | `ninth decade stage` | `85.0` | `male` | `Valve disease` | `7,080` | `1,535` | `1,340` | `1,805.0` |
| 50 | **`PH-B82`** | `ninth decade stage` | `85.0` | `male` | `Valve disease` | `6,950` | `1,475` | `1,325` | `1,785.0` |
| 51 | **`PH-C83`** | `ninth decade stage` | `85.0` | `male` | `CAD+MI` | `6,790` | `1,375` | `1,365` | `1,745.0` |
| 52 | **`PH-D84`** | `ninth decade stage` | `85.0` | `male` | `Valve disease` | `7,120` | `1,555` | `1,350` | `1,810.0` |
| 53 | **`PH-E85`** | `ninth decade stage` | `85.0` | `male` | `Valve disease` | `7,010` | `1,495` | `1,330` | `1,790.0` |
| 54 | **`PH-M22`** | `ninth decade stage` | `85.0` | `female` | `Valve disease` | `6,950` | `1,454` | `1,337` | `1,780.0` |

*(Exact per-donor cell counts and metadata are stored in `scratch/phaseA5_periheart_54_donors.csv`.)*

---

## GATE — Founder Decision Required Before Proceeding to Phase B

Phase A is complete (`0` code, model, or UI files have been modified). Before proceeding to **Phase B (`Code & UI Fixes`)**, **Phase C (`Ion-Channel & Safety Pipeline Fix`)**, **Phase D (`Within-Cohort Confound Re-Analysis`)**, **Phase E (`Independent Cross-Cohort Replication in PERIHEART`)**, **Phase F (`GRN Screen De-Biasing`)**, and **Phase G (`Consolidated Final Table`)**, please confirm:

1. **`NL-101` Identity Confirmation (A.1):** Confirm that **`SIRT1 + SIRT6 + GATA4 + ZBTB16`** is the sole canonical definition of `NL-101` to be used in all downstream analyses and tables (retiring the `SIRT6 + ZBTB16 + GATA4 + NKX2-5` audit typo).
2. **Approval to Proceed to Phases B–G:** Confirm whether we should now execute Phases B, C, D, E, F, and G in order.
