# Zenith / Nilus Lab — Phase 2 Code & UI Remediations (`code_ui_fixes.md`)

**Date:** 2026-09-22  
**Status:** COMPLETE — ALL PHASE 2 GATES & TESTS PASSED  
**Test Script:** `<repo>/scripts/run_phase2_test.py`  
**Verified Output JSON:** `<repo>/scratch/phase2_prompt1_verified_output.json`

---

## 2.1 Removal of `r = 0.999` Rule & Server-Side Validation Guard

### Code Changes Applied (`<repo>/bridge_server.py:7355–7545`)
1. **Removed `r = 0.999` Instruction:**
   - Deleted the `0.999` rule from `system_base` (`bridge_server.py:7392–7400`). Zero instances of `0.999` remain anywhere in `bridge_server.py`.
   - Replaced with the mandatory constraint:
     > *"Select only genes present in the provided correlation table and report their exact r from that table. Never output a gene absent from the table. Never invent a correlation value."*
2. **4-Decimal Table Precision:**
   - Updated `pro_str` and `aging_str` (`bridge_server.py:7364–7371`) from `.3f` to `.4f` so the LLM receives the exact 4-decimal `r` values stored in `models/cell_type_genes.json`.
3. **Hard Server-Side Guard (`_validate_panel_against_table`, `bridge_server.py:7416–7432`):**
   - Built `source_table_lookup` mapping every valid HGNC symbol in `pro_genes + aging_genes` (`100` genes for specialist cell types) to its exact float `correlation`.
   - Every candidate panel (`A`, `B`, `C`), the `Refined Panel`, and the `Final Response Gate` (`bridge_server.py:7538–7542`) are validated against `source_table_lookup`. Any off-table gene symbol or correlation discrepancy (`|r_emitted - r_table| > 0.0015`) **rejects** the panel (`ValueError` / `HTTP 422`), preventing any non-looked-up gene or correlation from ever being emitted.

### Phase 2.1 Verification Test Output (`scripts/run_phase2_test.py`)
Re-ran the exact prompt naming `ZBTB16, FOXO3, MEF2C, PPARGC1A, ATP2A2, RYR2, SCN5A, GJA1, MYH7`:
- **`[Check 1]`** `'0.999'` present anywhere in `bridge_server.py`: **`False`**
- **`[Check 2]`** Adversarial Off-Table Injection (`ZBTB16 r=0.999`): **`PASS — Rejected by server-side guard`**
- **`[Check 3]`** Adversarial Correlation Tampering (`TTN-AS1 r=0.4500` vs table `0.3002`): **`PASS — Rejected by server-side guard`**
- **`[Check 4]`** Live `POST /api/gpt-discovery/run` on Prompt 1 (`regular_ventricular_cardiac_myocyte`):
  - **HTTP Status:** `200 OK`
  - **Returned Genes (All 100% on-table, zero `0.999` values):**

| Gene Symbol | Emitted `r` | Source Table `r` (`cell_type_genes.json`) | Absolute Diff | Direction |
|---|---:|---:|---:|---|
| **`TTN-AS1`** | `+0.3002` | `+0.3002` | `0.0000` | `UP_IN_YOUNG` |
| **`PRKCE`** | `+0.1911` | `+0.1911` | `0.0000` | `UP_IN_YOUNG` |
| **`SLC8A1-AS1`** | `+0.1904` | `+0.1904` | `0.0000` | `UP_IN_YOUNG` |
| **`HSPB1`** | `-0.4182` | `-0.4182` | `0.0000` | `UP_IN_AGED` |

---

## 2.2 Disabling Lab-Action Exports (OT-2 & Wet-Lab Dossier)

- **Backend Routes Disabled (`HTTP 403`):**
  - `<repo>/bridge_server.py:5321–5327` (`POST /generate_opentrons_protocol`)
  - `<repo>/bridge_server.py:8061–8067` (`POST /api/v2/robotics/opentrons`)
  - `<repo>/bridge_server.py:8070–8076` (`POST /api/v2/dossier/generate`)
- **Frontend UI Buttons & Handlers Disabled:**
  - `<repo>/index.html:6142–6143`: Added `disabled` attribute and `"Disabled pending wet-lab validation"` tooltip to `"Export OT-2 Script (Disabled)"` and `"Print Wet-Lab Dossier (Disabled)"`.
  - `<repo>/index.html:6551–6558`: Replaced `window.printClinicalDossier` and `window.downloadOpentronsScript` implementations with explicit user alerts stating that exports are disabled until underlying predictions are wet-lab validated.

---

## 2.3 Neutralizing Arrhythmia Safety Claims

- **Code & UI Changes (`<repo>/index.html:2148–2168`):**
  - Removed `"NEUROS-X Arrhythmia Safety Engine"`, `"512-Node Cardiac Syncytium (ESI Conduction Substrate)"`, and `"VERIFIED SAFE — STABLE CONDUCTION"`.
  - Replaced with:
    - **Header:** `"512-Node Leaky Integrate-and-Fire (LIF) Oscillator Heuristic"` (`Illustrative Network Toy Model`)
    - **Badge:** `"LIF OSCILLATOR STATE: SYNCHRONOUS (ILLUSTRATIVE HEURISTIC ONLY)"`
    - **Stated Limitation:** *"Simulates a 512-node leaky integrate-and-fire (LIF) oscillator network with no action-potential morphology and no spatial cardiac tissue domain. Cannot assess clinical arrhythmia risk, Long QT, conduction block, or rotor formation."*
- **Cell-Type Gating Assessment:**
  - In `<repo>/bridge_server.py:7628` and `<repo>/index.html:6151`, `arrhythmia_safety` was previously called unconditionally for all cell-type queries (including `fibroblast` and `endothelial_cell`). It is an ungated global call to `services/neuros_substrate_service.py`.

---

## 2.4 Relabeling the LNP Panel

- **Code & UI Changes (`<repo>/index.html:2070–2146`):**
  - Relabeled header from `"mRNA-LNP Formulation Delivery Optimizer"` to **`"Illustrative LNP Formulation Parameter Explorer"`** (`Slider-Driven Heuristic`).
  - Replaced `"Status: OPTIMIZED_DELIVERY"` and `"Target: Heart (Cardiomyocytes)"` with **`"Mode: ILLUSTRATIVE_EXPLORER"`** and **`"Note: Outputs depend on slider positions only, independent of gene cocktail."`**

---

## 2.5 Full UI Number Inventory (`index.html` & `bridge_server.py`)

Every figure displayed on the Zenith Discovery workstation dashboard traced to `file:line`:

| Dashboard Widget / Metric | Exact Source (`file:line`) | Classification | What Produces It |
|---|---|---|---|
| **Tournament Discovery — Cell Count** (`125,289` vCMs, `59,341` fibroblasts) | `bridge_server.py:7358–7365` | **LOOKED UP** | Read from `models/cell_type_genes.json` (`ct_data["n_cells"]`), computed on Google Colab from the 486,134-cell Litviňuková HCA `.h5ad`. |
| **Tournament Discovery — `"3 competing panels, 2 refinement rounds"`** | `bridge_server.py:7440, 7533` | **COMPUTED / STATIC** | Runs 3 parallel `gpt-4o` calls (`Panel A, B, C` at `temp=0.0`) + 1 judge call + 1 refinement call (`rounds_completed = 2`). |
| **Tournament Discovery — `"Conf: 80% / 85% / 90%"`** | `bridge_server.py:7489` | **LLM-GENERATED** | `judge_result.get("confidence", 0.8)` emitted by the `gpt-4o` Judge prompt. |
| **Tournament Discovery — `"5,009D HD Manifold"`** | `index.html:6084` | **STATIC** | Hardcoded badge in `index.html:6084` referring to the `5,009` HVG vocabulary of `models/scvi_model_486k_real`. |
| **Tournament Discovery — `"100 Differential Candidates"`** | `bridge_server.py:7362–7363` | **LOOKED UP** | `len(pro_genes[:50]) + len(aging_genes[:50]) = 100` genes passed in `gene_context` from `models/cell_type_genes.json`. |
| **Tournament Discovery — `"Age Δ (epigenetic)"` (`-0.1y`, `-0.5y`)** | `bridge_server.py:7366` | **LOOKED UP** | Read from `models/cell_type_genes.json` (`ct_data["age_delta_years"]`), which was computed in `extract_celltype_genes.py:133–135` via `models/age_clock.pkl` (`clock.predict(aged_centroid) - clock.predict(young_centroid)`). |
| **Tournament Discovery — Candidate Gene `r` Values** | `bridge_server.py:7362–7363` + `_validate_panel_against_table` | **LOOKED UP (Guarded)** | Looked up from `models/cell_type_genes.json` and now strictly enforced by `_validate_panel_against_table` (`bridge_server.py:7416`). |
| **GRN Weight Overlays (`+1.50/+1.30/+1.20` vs `+0.11/+0.12/+0.11`)** | `index.html:6193–6222` & `index.html:4680–4755` (`BiosimBridge.renderGraphRAG`) | **SLIDER / CORRELATION HEURISTIC** | **Resolved:** In `index.html:6209–6222`, if a discovered gene matches a slider key (`GATA4, MEF2C, TBX5, NKX2-5, MYC, SNAI1`), its slider is set (`corr * 3.0`), yielding high weights (`+1.50/+1.30/+1.20`). When none of the discovered genes match those 6 hardcoded TF slider names (as in Blind Prompts 1 & 2), all 6 sliders remain `0.0`, and `renderGraphRAG` falls back to scaling the correlation scores (`~0.11–0.12`)! |
| **Transcriptomic Factor Weight Explorer (formerly labeled `scGPT`)** | `index.html:1680` & `index.html:4560–4650` (`runMultiOmicsPredictor`) | **SLIDER-DERIVED** | `scGPT` is **never invoked**. JavaScript function `runMultiOmicsPredictor()` in `index.html` computes closed-form arithmetic from the 6 TF sliders (`slider-gata4`..`slider-snai1`) and 5 drug checkboxes (`chk-semaglutide`..`chk-pitavastatin`). |
| **`TIME-seq CpG Delta`, `Transcriptome Stability`, `Sirtuin Activity`, `Endothelial Rejuv`, `Syncytial Safety`, `AFRAID Frailty Age`** | `index.html:1960–1998` & `index.html:4580–4640` | **SLIDER-DERIVED** | Computed in browser JavaScript inside `runMultiOmicsPredictor()` as linear combinations of the UI sliders and checkboxes. |
| **Clinical Trial Panel (`DunedinPACE`, `DamAge`, `AdaptAge`)** | `index.html:2001–2024` & `index.html:4610–4635` | **SLIDER / CHECKBOX LOOKUP** | Computed in browser JavaScript by summing constant offsets assigned to the 5 intervention checkboxes (`chk-semaglutide`, `chk-omega3`, etc.) and TF sliders. |
| **Expression Profile List (`GATA4 +125%`, `MYH6 +90%`, `COL1A1 -58%`, etc.)** | `index.html:2063` & `index.html:4638–4665` | **SLIDER-DERIVED / STATIC** | Browser JavaScript array in `runMultiOmicsPredictor()` that scales fixed base percentages (`+125%`, `+90%`, `-58%`) by the active slider positions. |
| **LNP Formulation Panel (`94.4%`, `0.915`, `23.9%`, `12.2%`, `17.0h`, `8.8%`)** | `index.html:2071–2146` & `index.html:4760–4830` (`runLNPOptimizer`) | **SLIDER-DERIVED** | Computed entirely from the 6 LNP lipid sliders (`Ionizable=50%`, `Cholesterol=38.5%`, `Helper=10%`, `PEG=1.5%`, `N/P=6.0`, `chk-lnp-active=true`). Completely independent of the gene cocktail. |
| **512-Node Arrhythmia / LIF Panel (`Phi_hat`, `Synchrony`, ECG trace)** | `services/neuros_substrate_service.py:240–430` | **COMPUTED (Toy LIF Model)** | Runs a 512-node leaky integrate-and-fire ODE step over ion channel expression proxies (`predict_factor_effect`). Since `SCN5A/KCNH2/RYR2` Ensembl IDs were unmapped in `gene_to_idx` (`task-15500.log:36-51`), `ion_expr` defaults to `0.0`, returning the baseline `"SAFE"` state every time. |
| **`"V30.1 GOLD VALIDATED"` / `"v33.4_GOLD"`** | `index.html:6884, 6892` | **STATIC** | Hardcoded HTML strings in the footer/modal templates. |
