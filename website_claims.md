# Zenith / Nilus Lab — Phase 1 Public Website Audit (`website_claims.md`)

**Date:** 2026-09-22  
**Scope:** `niluslab.com` (`<repo>/index.html`), `/how_it_works.html` (`<repo>/how_it_works.html`), `/technical_catalog.html` (`<repo>/technical_catalog.html`), and pitch decks (`<repo>/NILUS_MASTER_PITCH_V2.html`).  
**Compliance:** All claims traced to exact files, line numbers, checkpoints, or external DOIs. Every claim is marked **SUPPORTED**, **RESTATE** (with exact corrected wording), or **REMOVE**.

---

## 1.1 Directly Falsifiable Architecture & Dataset Claims

| Public Claim | Where Stated (`file:line`) | Actual Verified Value | Source of Truth | Verdict & Action |
|---|---|---|---|---|
| **`"~500M parameters"` / `"ULTRA-500M"` / `"3.03B parameters"`** | `technical_catalog.html:380, 486, 2429, 5697`<br>`CATALOG_AUDIT_2026_01_24.md:8` | • **Specialist scVI:** **`2,649,170` parameters** (`14.24 MB`)<br>• **Foundation scVI v1:** **`37,234,698` parameters** (`166.77 MB`)<br>• **Foundation scVI v29:** **`31,660,338` parameters** (`126.81 MB`)<br>• `ZenithSDE` (`bridge_server.py:512-538`): un-trained PyTorch class with **no `.pt` checkpoint** | `<repo>/models/scvi_model_486k_real/model.pt`<br>`<repo>/models/zenith_foundation_v1/model.pt`<br>`<repo>/models/zenith_foundation_v29/model.pt` | **RESTATE:** Replace `"~500M"` and `"3.03B"` with **`"2.65M parameters (Specialist Cardiac scVI VAE) and 37.23M parameters (Multi-Atlas Foundation scVI VAE)"`**. |
| **`"16 attention heads, 12-layer encoder"` / `"45-Layer Residual Transformer Trunk"`** | `technical_catalog.html:1309, 514` | **Zero attention heads.**<br>• `scvi_model_486k_real`: `2`-layer MLP encoder/decoder (`n_hidden=128, n_latent=20`)<br>• `zenith_foundation_v1`: `4`-layer MLP encoder/decoder (`n_hidden=1024, n_latent=64`) | `model.pt` `attr_dict['init_params_']` (`scvi-tools` ZINB/NB VAE) | **RESTATE:** Replace all `"Transformer"` / `"16 attention heads, 12-layer"` descriptions with **`"2-layer (128-unit) and 4-layer (1,024-unit) Variational Autoencoder (scVI) MLP architectures"`**. |
| **`"486,134 real human cardiac cells"`** | `technical_catalog.html:562, 612, 6993` | • **Source HCA Atlas (Colab):** `486,134` cells (`extract_celltype_genes.py` computed `cell_type_genes.json` on all `486,134` cells)<br>• **Specialist scVI Training Set:** **`99,993` cells** (stratified 100k subsample across 14 donors via `train_real_486k_scvi_rebuild_colab.py`)<br>• **Local Bundled `.h5ad`:** **`18,641` cells** (`5,307` vCMs, `2,446` fibroblasts) | `<repo>/extract_celltype_genes.py:21`<br>`<repo>/train_real_486k_scvi_rebuild_colab.py:48`<br>`<repo>/models/scvi_model_hca/adata.h5ad` | **RESTATE:** State explicitly: **`"Gene correlations derived from the 486,134-cell Litviňuková et al. (2020) Heart Cell Atlas; Specialist scVI model trained on a donor-stratified 99,993-cell subsample; 18,641-cell reference subset bundled locally."`** |
| **`"400 epochs"`** | `technical_catalog.html:564, 612`<br>`ZENITH_FOUNDATION_MODEL_CARD.md:83` | • `scvi_model_486k_real`: **`100` epochs** (`ELBO 648.56 -> 519.34`)<br>• `zenith_foundation_v1`: **`150` epochs** (`train_loss 1111.31 -> 892.80`)<br>• `zenith_foundation_v29`: **`2` epochs** | `model.pt` `attr_dict['history_']` | **RESTATE:** Change `"400 epochs"` to **`"100 epochs (Specialist 99.9k model) and 150 epochs (Foundation 1.96M model)"`**. |
| **`"2.42M cells"`** | `index.html:7, 11, 18, 2175, 3636, 4171, 4403, 6630`<br>`how_it_works.html:239`<br>`technical_catalog.html:466, 9602` | **`1,962,128` cells** in `zenith_foundation_v1/model.pt` registry (`field_registries['X']['summary_stats'] = {'n_vars': 5858, 'n_cells': 1962128}` across `14` batches streamed via CELLxGENE Census). *(Note: `1,962,128 + 486,134 = 2,448,262`, which appears to be the origin of `"2.42M"`, though Litviňuková is already inside CELLxGENE).* | `<repo>/models/zenith_foundation_v1/model.pt` | **RESTATE:** Replace `"2.42M cells"` with **`"1,962,128 cells in the CELLxGENE Foundation scVI checkpoint (and 486,134 cells in the Litviňuková Heart Cell Atlas)"`** and clarify that live Tournament Discovery runs on the Litviňuková 14-donor Specialist tables. |
| **`"92% real / 8% synthetic"`** | `technical_catalog.html:10342` | • `run_zenith_screening_pipeline.py` used **`0%` real cells (`100%` synthetic Gaussian arrays)**.<br>• Part 2 real GRN screen (`run_part2_real_screen.py`) uses **`100%` real cells (`5,307` vCMs)**.<br>• `"92%"` in `ZENITH_FOUNDATION_MODEL_CARD.md:147` is actually the **marker gene recovery score (`92%`)** across 5 cell types, not a cell ratio. | `<repo>/ZENITH_FOUNDATION_MODEL_CARD.md:147` | **REMOVE / RESTATE:** Remove `"92% real / 8% synthetic"`. State the exact dataset used by each workflow (`100% real HCA single-cell profiles` for empirical lookups/GRN screen; `synthetic ODE/agent simulation` for visual viewport). |
| **`"5,009-dimensional HD manifold"`** | `index.html:3636, 4054, 4062, 6084, 6629`<br>`technical_catalog.html:402, 494, 530` | • **Latent manifold dimension:** **`20-D`** (`scvi_model_486k_real`) or **`64-D`** (`zenith_foundation_v1`)<br>• **Input gene vocabulary:** **`5,009` genes** (`5,000` HVGs + `9` protected cardiac ion channel genes from `train_real_486k_scvi_rebuild_colab.py`) | `<repo>/train_real_486k_scvi_rebuild_colab.py:95-125` | **RESTATE:** Change `"5,009D HD Manifold"` to **`"20-D scVI Latent Manifold (5,009 HVG Input Vocabulary)"`**. |

---

## 1.2 Unsourced Benchmark Numbers

Every benchmark below was searched across all Python scripts, `.json` reports, and model checkpoints:

| Public Benchmark Claim | Where Stated (`file:line`) | Actual Computation / Backing File | Verdict |
|---|---|---|---|
| **`99.8% fidelity` / `99.8% stability index`** | `technical_catalog.html:2417, 9842` | **None.** Mean-gene scVI reconstruction correlation on `adata.h5ad` is **$r = 0.7514$** (`asset_verification.md`). `REPRO_MANIFEST.json:149` has a static literal `"fidelity_score": 0.992`. | **REMOVE** (or replace with verified mean-gene reconstruction $r = 0.7514$). |
| **`98.2% causal fidelity (GRN v4.0)`** | `technical_catalog.html:768`<br>`bridge_server.py:8421` | **None.** Hardcoded string in `bridge_server.py:8421` and HTML. | **REMOVE** |
| **`280% increase in predictive stability`** | `technical_catalog.html:11530` | **None.** Marketing literal in HTML with no holdout benchmark script. | **REMOVE** |
| **`R = 0.982 (BiT Age)`** | `technical_catalog.html:7363` | **Misapplied citation.** $R \approx 0.98$ is Meyer & Schumacher's (2021) reported correlation in *C. elegans* nematode bulk RNA-seq, not a holdout evaluation of Zenith on human cardiac cells (`services/bit_age_clock.py:10`). Our 14-donor LODO Ridge cardiac clock has **Test MAE = `6.85 years`** ($r \approx 0.58$). | **REMOVE / RESTATE** (cite LODO MAE = `6.85 years` on 14 HCA donors). |
| **`99.0% conformal coverage`** | `technical_catalog.html` | **None.** No conformal prediction calibration script or holdout set exists. | **REMOVE** |
| **`99.2% ESI`** | `REPRO_MANIFEST.json:149` / Deck | **None.** Static constant (`0.928` in `run_zenith_screening_pipeline.py:295`, `0.9483` via rule-based formula). | **REMOVE** |
| **`94% LNP cardiac tropism` (`94.4%`)** | `index.html` / `services/lnp_optimizer.py` | **Slider-derived heuristic.** Computed from UI slider defaults (`PEG=1.5%, Ionizable=50%, Cholesterol=38.5%, Helper=10%`) independently of the gene cocktail. | **REMOVE** from homepage/claims; relabel UI widget as illustrative explorer. |
| **`0.4ms GPU memory latency`** | `technical_catalog.html` | **None.** No hardware benchmark log exists. | **REMOVE** |
| **`Genomic Stability Index >95%`** | `index.html` / `js/script.js:1225` | **Frontend heuristic:** `stability = max(0, 100 - (totalDamage / agents.length) * 100)`. | **RESTATE** as an illustrative simulation state variable, not an empirical genomic assay. |

---

## 1.3 Regulatory & Validation Language

| Term / Badge | Locations (`file:line`) | Assessment & Required Action |
|---|---|---|
| **`"Safety Tier: CLINICAL+"`** | `technical_catalog.html:502` | **REMOVE.** Contradicts `"Research Use Only (RUO)"` and implies human clinical safety clearance. |
| **`"Phase 4 validated"` / `"PHASE 4 VALIDATED"`** | `index.html:3213`<br>`technical_catalog.html:2409, 14092, 14194, 14300, 14307` | **REMOVE.** In regulatory medicine, "Phase 4" means post-marketing surveillance of an FDA-approved therapy. In the codebase, "Phase 4" merely referred to internal sprint 4 (`tests/test_phase4_engines.py`). Must be renamed to `"Module 4 (In-Silico PK/PD Simulation)"`. |
| **`"Safety Cleared"` / `"VERIFIED SAFE"`** | `index.html:2160, 6267, 6612`<br>`services/neuros_substrate_service.py:422` | **REMOVE.** Replace with `"Simulated LIF Network State: Nominal (Heuristic Only — Not a Clinical Arrhythmia Assay)"`. |
| **`"2.42M Integrated Ensemble Validated"`** | `index.html:2175, 3636, 6630` | **REMOVE / RESTATE** to `"1.96M-Cell CELLxGENE scVI Checkpoint + 14-Donor HCA Reference"`. |
| **`"Horvath Clock Validated"` / `"Decoder Validated (High-Fidelity)"`** | `index.html` / `technical_catalog.html` | **REMOVE `"Validated"`.** `services/horvath_clock.py` applies linear probe weights to transcriptomic proxies, not bisulfite CpG methylation arrays. |
| **`"V30.1 GOLD VALIDATED"` / `"Audit: v33.4_GOLD [PASS]"`** | `index.html:6884, 6892`<br>`technical_catalog.html:907` | **REMOVE.** Internal build tags styled as external regulatory audit passes. |
| **`"three completed autonomous experiments"`** | `index.html` / `technical_catalog.html` | **RESTATE:** Change `"experiments"` to **`"in-silico simulation runs"`**. |

---

## 1.4 Reconciliation of the Six Age-Reversal Figures

| Figure | Where It Appears | Exact Code / File Origin | Defensibility Verdict |
|---|---|---|---|
| **`-14.2 years`** | Homepage (`index.html`) | Static marketing literal in HTML. | **UNSUPPORTED — REMOVE** |
| **`-13.0 years`** | Pitch deck (`NILUS_MASTER_PITCH_V2.html`) & `run_zenith_screening_pipeline.py:293` | Hardcoded override `res['age_reversal_delta'] = 13.00` in `run_zenith_screening_pipeline.py:293`, which mistook the **13.0-year hard cap (`FIX 6`)** for an empirical output. | **UNSUPPORTED — REMOVE** |
| **`Capped at 13.0 years`** | `technical_catalog.html:6673-6709` (`FIX 6`) & `bridge_server.py:4703, 6704` | `MAX_AGE_REDUCTION_YEARS = 13.0` (`age_reduction = min(raw_age, 13.0)`), an engineering clamp placed on GPT-4o outputs citing Sarkar et al. (2020). | **SUPPORTED AS A CAP ONLY** — Never cite `13.0y` as a model discovery result. |
| **`"Validated at -12"` (`-12.0y`)** | `index.html:1258, 2429` & `how_it_works.html:208` | Static preset baseline delta in frontend simulation JS. | **UNSUPPORTED — REMOVE** |
| **`-35.2 years`** | `technical_catalog.html:4649` (`DRP-Alpha-12`) | `CATALOG_AUDIT_2026_01_24.md:24-27`: arithmetic difference between synthetic normalized `bioAge = 0.80` (60 yo) and target `0.1011` (25 yo) in the 2D canvas simulator. | **UNSUPPORTED — REMOVE** (already flagged as synthetic in `CATALOG_AUDIT_2026_01_24.md`). |
| **`+15.45y` / `+5.85y`** | `run_zenith_screening_pipeline.py` (with / without line 108 `+1.65` bonus) | Rule-based 15-gene weighted sum with `+1.65` hardcoded synergy multiplier for `{SIRT1, SIRT6, GATA4, ZBTB16}` and `-92%` senescence clamp (`verification_results.md`). | **UNSUPPORTED — REMOVE** |

> **Single Defensible Statement:**
> *"In donor-holdout cross-validation across the 14 human donors of the Litviňuková et al. (2020) Heart Cell Atlas (`5,307` ventricular cardiomyocytes), a Leave-One-Donor-Out (LODO) transcriptomic Ridge clock predicts chronological donor age with **Test MAE = 6.85 years**. Under circularity-free GRN propagation (`CollecTRI + DoRothEA + TRRUST v2`, `22,635` active cardiac edges), candidate 4-TF perturbations shift aged cardiomyocyte transcriptional profiles by **up to +6.07% toward the young-donor expression centroid** (equivalent to **-0.1 to -0.6 years** on the latent ElasticNet clock `models/age_clock.pkl`). No multi-year epigenetic age reversal has been validated in wet-lab cells."*

---

## 1.5 Third-Party Attributions & Citations Verification

| Citation | Resolves? | Verification & Accuracy Assessment | Action Required |
|---|---|---|---|
| **Johnson & Sinclair, *Frontiers in Genetics* (May 29, 2026)**<br>`DOI: 10.3389/fgene.2026.1836446` | **YES (Real Paper)** | *Title:* `"Turning back time: a comprehensive list of interventions that decrease next-generation epigenetic aging clocks in humans"` by Adiv A. Johnson & David A. Sinclair. Reviews published human trials (e.g., Semaglutide, Omega-3). **Misuse in UI (`index.html:2004, 2022`):** The UI attributes `DunedinPACE / DamAge / AdaptAge` numbers displayed during in-silico cocktail discovery to `"Adiv A. Johnson & Harvard Genetic Studies"`. Neither Johnson nor Harvard endorsed or computed outputs for Zenith's gene cocktails. | **REMOVE attribution of platform outputs to Adiv A. Johnson & Harvard Genetic Studies.** Keep the citation solely in documentation if referencing published human clinical trial benchmarks. |
| **Haghani et al., *GeroScience* (Aug 2025 / 2026)**<br>*EnsembleAge* | **YES (Real Paper)** | *Title:* `"EnsembleAge: enhancing epigenetic age assessment with a multi-clock framework"` (*GeroScience*, Aug 2025). However, `EnsembleAge` is a DNA methylation array framework across >200 mouse/cross-species perturbation datasets, whereas `services/cardiac_ensemble_clock.py` applies heuristic rules to scRNA-seq mRNA counts. | **RESTATE:** Clarify that `cardiac_ensemble_clock.py` is an internal transcriptomic proxy inspired by multi-clock ensembling, not the published Haghani CpG methylation array model. |
| **Krolevets et al., *EBioMedicine* (2023, cited as 2026)** | **YES (Real Paper, Wrong Year)** | *Title:* `"Global and regional DNA methylation patterns in heart failure: a case-control analysis"` (*EBioMedicine*, 2023). Measures bisulfite/array DNA methylation in heart failure biopsies, not scRNA-seq transcriptomics. | **RESTATE:** Fix year (`2023`) and clarify that Zenith measures mRNA expression, not CpG methylation at the 8 Krolevets loci. |
| **Griffin et al., *Nature Aging* (2024)**<br>*TIME-seq* | **YES (Real Paper)** | *Title:* `"TIME-seq reduces time and cost of DNA methylation measurement for epigenetic clock construction"` (*Nature Aging*, 2024). Wet-lab targeted bisulfite sequencing protocol. Zenith has no TIME-seq methylation data. | **REMOVE** claims that Zenith monitors `"TIME-seq CpG methylation loci across the simulation trajectory"` (`technical_catalog.html:12582`). |
| **Meyer & Schumacher, *Aging Cell* (2021)**<br>*BiT Age (`e13320`)* | **YES (Real Paper, *C. elegans*)** | Developed as a binarized transcriptomic clock in ***Caenorhabditis elegans* (nematodes)**. `services/bit_age_clock.py:29-50` uses hand-coded Python thresholds (`"SIRT1": 2.10`, etc.), not trained human ventricular cardiomyocyte BiT Age weights. | **RESTATE:** Disclose that `BiTAgeClockService` is a custom binarized transcriptomic heuristic, not a validated human cardiac clock. |

---

## 1.6 Capability Claims & API Endpoint Classification

Inspection of all 7 advertised capability modules in `<repo>/routers/` and `<repo>/services/`:

| Advertised Endpoint / Capability | Router & Service File (`file:line`) | Classification | What It Actually Computes in Code |
|---|---|---|---|
| **ADMET Screening** (`/api/v1/admet/*`) | `routers/admet_router.py`<br>`services/admet_engine.py` (`482 lines`) | **HEURISTIC / RULE-BASED** | Regex/substring matching on SMILES strings (`Lipinski Ro5`, Crippen-Wildman fragment constants, SMARTS-like string alerts). No RDKit 3D conformers or ML QSAR model. |
| **CRISPR Prime-Editor Design** (`/api/v1/prime-editor/*`) | `routers/prime_editor_router.py`<br>`services/prime_editor_engine.py` (`217 lines`) | **HEURISTIC / RULE-BASED** | String slicing for 20-nt spacer + 80-nt Cas9 scaffold + GC-content/melting-temperature ($T_m$) arithmetic formula (`DeepPrime` score is a closed-form GC/length formula, not the DeepPrime neural network). |
| **Molecular Docking** (`/api/v1/docking/*`) | `routers/docking_router.py`<br>`services/docking_engine.py` (`219 lines`) | **STUB / ANALYTICAL APPROXIMATION** | Closed-form algebraic equation summing simplified Lennard-Jones/H-bond heuristics from amino-acid composition. Does **not** run AutoDock Vina or 3D spatial coordinate docking. |
| **Mendelian Randomisation** (`/api/v1/causal-mr/*`) | `routers/causal_mr_router.py`<br>`services/mendelian_randomisation_engine.py` (`328 lines`) | **LOOKUP + ALGEBRAIC RATIO** | Looks up curated GWAS beta weights (`GWAS_INSTRUMENTS` dict in Python) and computes Wald ratio / IVW algebra over that static dictionary. |
| **Multi-Omics Integration** (`/api/v1/multiomics/*`) | `routers/multiomics_router.py`<br>`services/multiomics_integration_engine.py` (`312 lines`) | **HEURISTIC / LOOKUP** | Computes weighted averages over a static `BIOLOGICAL_LATENT_FACTOR_DB` dictionary in Python. |
| **Polygenic Risk Scoring (PRS)** (`/api/v1/prs/*`) | `routers/polygenic_risk_router.py`<br>`services/polygenic_risk_engine.py` (`271 lines`) | **LOOKUP + LINEAR SUM** | Sums $\sum \beta_i G_i$ across a 25-SNP hardcoded dictionary (`GWAS_BETA_CATALOG`). |
| **Virtual Adaptive Trials (`N=1,000` Digital Twins)** (`/run_virtual_trial`) | `routers/virtual_trial_router.py`<br>`services/virtual_trial_engine.py` (`241 lines`) | **PARAMETRIC MONTE CARLO** | Samples 1,000 synthetic scalar numbers (`random.gauss`) in a 2-compartment ODE formula. Does **not** simulate 1,000 single-cell scVI transcriptomic profiles. |

> **Action:** None of these 7 endpoints may be advertised as deep-learning or structural-biology pipelines; any retained endpoint must be labeled as a **Rule-Based / Analytical Prototype Calculator**.

---

## 1.7 Version Consistency Audit

Currently deployed pages display conflicting version strings:
- `index.html`: `v26` (`is-chrp-v26-generative`), `V30.1 GOLD VALIDATED` (`L6884`), `v33.4_GOLD` (`L6892`)
- `technical_catalog.html`: `v30.0`, `v31.0 GOLD` (`L466`), `v31.1`, `v33.4` (`L907`)
- `perturbation_engine.py`: `v28` (`L10`)
- `ZENITH_FOUNDATION_MODEL_CARD.md`: `v29` (`L1`)

**Action:** Standardize all user-facing HTML headers and footers to a single version string without `"GOLD VALIDATED"` badges: **`Zenith Research Preview (v31.0-RUO)`**.
