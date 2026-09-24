# Zenith — Phase C Deliverable: Ion-Channel Mapping Bug Fix (`ion_channel_fix.md`)

**Verification Script:** `scripts/run_phaseC_ion_channel_test.py`  
**Output Artifact:** `scratch/phaseC_ion_channel_results.json`

---

## C.1 Root Cause Analysis of the Bug

`train_real_486k_scvi_rebuild_colab.py` forced cardiac ion-channel genes into `models/scvi_model_486k_real`'s `5,009`-gene HVG vocabulary (`models/scvi_model_486k_real/gene_index.json`). However, every call to `PerturbationEngine.predict_factor_effect()` (`perturbation_engine.py:493–501`) and `bridge_server.py:7674–7685` failed to resolve any ion-channel gene (`0 / 16` resolved), causing `ion_expr[gene]` to default to `0.0` and `CardiacNeuralSubstrate.encode_ion_profile()` (`services/neuros_substrate_service.py:217–218`) to substitute the hardcoded `HEALTHY_BASELINES` dictionary on every request.

Three compounded bugs caused this failure:

1. **Identifier-Space Mismatch in `gene_to_idx` (`perturbation_engine.py:89, 254` & `bridge_server.py:7675`):**
   - `models/scvi_model_486k_real/gene_index.json` stores `var_names` as **Ensembl Gene IDs (`ENSG00000...`)** (`5,009` entries).
   - `self.gene_to_idx` was constructed solely as `{g.upper(): i for i, g in enumerate(self.var_names)}` (`ENSG00000...` keys only).
   - Both `perturbation_engine.py:494` and `bridge_server.py:7675` iterated over `svc.substrate.ION_CHANNEL_GENES` (**HGNC symbols**: `"SCN5A"`, `"KCNH2"`, etc.) and checked `if gene in self.gene_to_idx:`, which evaluated to `False` for `100%` of symbols (`0 / 16` matched).
2. **Six Wrong Ensembl IDs Hardcoded in `cardiac_ion_channels` (`perturbation_engine.py:214–226`):**
   - Even in `self.ensembl_to_symbol`, `6` of the `11` entries in `cardiac_ion_channels` (`perturbation_engine.py:214–226`) contained **incorrect Ensembl IDs** that do not match GRCh38 or `d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad`:

| Ion-Channel Symbol | Wrong Ensembl ID in `perturbation_engine.py:214–226` | True GRCh38 Ensembl ID in `d4e69e01...h5ad` & `gene_index.json` | Index in `scvi_model_486k_real` (`5,009` genes) |
| :--- | :---: | :---: | :---: |
| **`KCNH2`** | `ENSG00000184489` *(Wrong)* | **`ENSG00000055118`** | `idx = 1590` |
| **`KCNJ2`** | `ENSG00000123700` *(Correct)* | **`ENSG00000123700`** | `idx = 4621` |
| **`SCN5A`** | `ENSG00000151140` *(Wrong)* | **`ENSG00000183873`** | `idx = 3336` |
| **`CACNA1C`** | `ENSG00000151067` *(Correct)* | **`ENSG00000151067`** | `idx = 843` |
| **`HCN4`** | `ENSG00000138622` *(Correct)* | **`ENSG00000138622`** | `idx = 3223` |
| **`KCNA5`** | `ENSG00000143842` *(Wrong)* | **`ENSG00000130037`** | `idx = 2549` |
| **`KCND3`** | `ENSG00000197965` *(Wrong)* | **`ENSG00000171385`** | `idx = 3861` |
| **`KCNIP2`** | `ENSG00000148818` *(Wrong)* | **`ENSG00000120049`** | `idx = 465` |
| **`RYR2`** | `ENSG00000198626` *(Correct)* | **`ENSG00000198626`** | `idx = 589` |
| **`SLC8A1`** | `ENSG00000183023` *(Correct)* | **`ENSG00000183023`** | `idx = 3587` |
| **`KCNQ1`** | `ENSG00000174776` *(Wrong)* | **`ENSG00000053918`** | `idx = 4553` |
| **`GJA5`** *(Connexin 40)* | *(Omitted)* | **`ENSG00000265107`** | `idx = 468` |

3. **Identifier Mismatch in `GRNAuthority.compute_network_influence` (`perturbation_engine.py:409`):**
   - `GRNAuthority.compute_network_influence(active_tfs, self.var_names)` was passed `self.var_names` (`ENSG...` IDs), whereas `models/celloracle_grn.csv` is indexed by **HGNC symbols**, causing `influence_vec` to return all zeros (`0.0`).

---

## C.1 Fix Applied & Pre-Fix vs Post-Fix Comparison Across 3 Cocktails

### Surgical Changes Made
1. Extracted all `5,009` exact `Ensembl ID -> HGNC Symbol` mappings from `data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad` (`var/_index` $\rightarrow$ `var/feature_name`) into `models/scvi_model_486k_real/ensembl_to_symbol.json`.
2. Updated `PerturbationEngine._populate_gene_mappings()` (`perturbation_engine.py:70–127`) to:
   - Load `models/scvi_model_486k_real/ensembl_to_symbol.json` and the `12` verified GRCh38 cardiac ion-channel Ensembl IDs (`11` protected channels + `GJA5`),
   - Dual-key `self.gene_to_idx` by **both** uppercase Ensembl ID (`ENSG00000183873`) and uppercase HGNC symbol (`SCN5A`), and
   - Pass `self.symbol_var_names` (`5,009` HGNC symbols) to `GRNAuthority.compute_network_influence()`.
3. Updated `services/neuros_substrate_service.py:96–124` to include all `11` protected cardiac ion channels (`KCNA5`, `KCND3`, `KCNIP2`, `SLC8A1` added alongside `SCN5A`, `KCNH2`, `KCNQ1`, `KCNJ2`, `CACNA1C`, `HCN4`, `RYR2`, `GJA5`), reset the LIF neuron state deterministically before each simulation (`services/neuros_substrate_service.py:246–251`), and replace `"SAFE"` / `"VERIFIED_SAFE"` / `"Cocktail approved for wet-lab validation."` with **`"EXPLORATORY_NOMINAL"`** (`services/neuros_substrate_service.py:380`, `bridge_server.py:7712`).

### Verification Results Across 3 Distinct Cocktails (`scripts/run_phaseC_ion_channel_test.py`)

| Condition / Cocktail | Resolved Channels in `gene_to_idx` | `SCN5A` ($\text{Na}_v1.5$) | `KCNH2` (hERG) | `CACNA1C` ($\text{Ca}_v1.2$) | `RYR2` | `KCNQ1` ($\text{K}_v7.1$) | `phi_hat` ($\hat{\Phi}$) | `synchrony` | `isi_variance` | Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Old Constant Baseline (Pre-Fix Bug)** | **`0 / 16`** *(All defaulted to `0.0` $\rightarrow$ `HEALTHY_BASELINES`)* | `3.0000` *(const)* | `3.5000` *(const)* | `2.5000` *(const)* | `3.0000` *(const)* | `3.0000` *(const)* | **`0.008892`** | **`0.033421`** | **`495.5399`** | `VERIFIED_SAFE` *(Invariant for all inputs)* |
| **Cocktail 1 (`NL-101`)**<br>`SIRT1 + SIRT6 + GATA4 + ZBTB16` | **`12 / 12`** (`100%` of in-vocab channels) | **`0.9231`** | **`3.3834`** | **`0.0500`** | **`0.0500`** | **`2.6248`** | **`0.044290`** | **`0.021086`** | **`299.6322`** | **`EXPLORATORY_NOMINAL`** |
| **Cocktail 2 (`Top GRN Quad`)**<br>`NFKB1 + MITF + CTCF + HIF1A` | **`12 / 12`** (`100%` of in-vocab channels) | **`0.0500`** | **`2.6382`** | **`0.0500`** | **`0.0500`** | **`0.0500`** | **`0.021269`** | **`0.034127`** | **`234.0872`** | **`BLOCKED`** *(`KCNQ1 < 0.5` LQT1 threshold)* |
| **Cocktail 3 (`Direct Ion Gain`)**<br>`SCN5A + KCNH2 + CACNA1C + RYR2` | **`12 / 12`** (`100%` of in-vocab channels) | **`119.6701`** | **`16.5453`** | **`89.6116`** | **`146.2661`** | **`34.6765`** | **`0.100612`** | **`0.011201`** | **`295.5766`** | **`BLOCKED`** *(`SCN5A, CACNA1C, RYR2` thresholds exceeded)* |

---

## C.2 Scope & Scientific Limitation Statement

Fixing the Ensembl-to-symbol lookup bug makes `PerturbationEngine` and the `512`-neuron Leaky Integrate-and-Fire (`LIF`) graph (`CardiacNeuralSubstrate`) respond dynamically and deterministically to the input cocktail's `scVI` and `GRN` perturbations across all `12` in-vocabulary cardiac ion-channel genes (`SCN5A, KCNH2, KCNQ1, KCNJ2, CACNA1C, HCN4, RYR2, KCNA5, KCND3, KCNIP2, SLC8A1, GJA5`).

**What this does NOT do:**
- It does **not** make `CardiacNeuralSubstrate` a biophysical cardiac electrophysiology or arrhythmia assay.
- The `512`-neuron Watts–Strogatz `LIF` network has no Hodgkin–Huxley / O'Hara–Rudy ionic currents ($I_{\text{Na}}, I_{\text{Kr}}, I_{\text{Ks}}, I_{\text{CaL}}$), no cardiac action-potential duration ($\text{APD}_{90}$) morphology, and no 2D/3D myocardial syncytium conduction velocity tensor.
- Accordingly, all `"VERIFIED_SAFE"` / `"approved for wet-lab validation"` strings have been removed from both backend (`services/neuros_substrate_service.py:380`, `bridge_server.py:7712`) and frontend (`index.html:2150–2162`), and replaced with **`"EXPLORATORY_NOMINAL"`** (`"Exploratory LIF substrate dynamics within nominal bounds (uncalibrated research proxy; not a clinical ECG or wet-lab safety assay)."`).

---

## C.3 Master Report Record Updated

The finding that every historical `VERIFIED SAFE` badge ever displayed by the platform was the result of an Ensembl-vs-HGNC symbol lookup failure (`0 / 16` ion channels matched, silently returning `0.0` and falling back to constant `HEALTHY_BASELINES`) has been added directly to the headline Negative Findings section of `zenith_phase0_to_phase4_master_report.md`.
