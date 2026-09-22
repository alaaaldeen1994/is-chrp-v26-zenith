# Zenith — Correct, Deploy, Verify (`deploy_and_correct.md`)

**Execution Date:** 2026-09-22 UTC  
**Deployed Commit SHA on `origin/main`:** `1fa73c0` (preceded by `fd75d72`, `031f660`, `664b399` from base `66edf8e`)  
**Live Deployment Host:** `https://niluslab.com/` (`server: railway-hikari`, `Last-Modified: Tue, 22 Sep 2026 19:17:05 GMT`)

---

## 1. Local Grep Table (Working Tree Verification — Steps 1.1–1.4)

### 1.1 Live Checkpoint Verification Summary
Both live PyTorch `model.pt` checkpoints (`models/scvi_model_486k_real/model.pt` and `models/zenith_foundation_v1/model.pt`) were inspected directly via `torch.load` (`attr.pkl` + `model_state_dict`) and reconciled across all HTML pages and reports:

| Metric | Specialist Checkpoint (`models/scvi_model_486k_real/model.pt`) | Foundation Checkpoint (`models/zenith_foundation_v1/model.pt`) |
| :--- | :--- | :--- |
| **Model Class & Likelihood** | `scvi.model.SCVI` (`gene_likelihood="zinb"`, `dispersion="gene"`) | `scvi.model.SCVI` (`gene_likelihood="nb"`, `dispersion="gene"`, `use_batch_norm="none"`) |
| **Hidden Layers (`n_layers`)** | **`2`** | **`4`** |
| **Hidden Channels (`n_hidden`)** | **`128`** | **`1,024`** |
| **Latent Dimensions (`n_latent`)** | **`20`** | **`64`** |
| **Gene Vocabulary (`n_vars`)** | **`5,009`** | **`5,858`** |
| **Registered Training Cells (`n_obs`)** | **`99,993`** (`89,994` train + `9,999` val, subsampled from the `486,134`-cell Litviňuková source atlas) | **`1,962,128`** (`1,765,916` train + `196,212` val) |
| **Pinned Parameter Convention (Trainable Float Parameters)** | **`3,268,462`** *(Footnote: `3,269,747` total tensor elements including `1,280` BatchNorm `running_mean`/`running_var` buffers and `5` `int64` `num_batches_tracked` counters; `2,626,668` active inference trainable parameters excluding unused `l_encoder`)* | **`37,234,698`** *(Footnote: equals total tensor elements as `use_batch_norm="none"`; `30,993,416` active inference trainable parameters excluding unused `l_encoder`)* |

### 1.2 Working Tree Forbidden-String Grep Table (`0` Occurrences Required)

Command executed:
```bash
python -c "import re; files = ['index.html', 'how_it_works.html', 'technical_catalog.html']; terms = ['500M', '3.03B', 'CLINICAL\\+', 'PHASE 4', 'GOLD', '2\\.42M', '99\\.8%', '98\\.2%', '280%', '0\\.982', 'VERIFIED SAFE', 'attention heads', 'Transformer', 'CERTIFIED'];
for f in files:
    txt = open(f, encoding='utf-8').read()
    c = {t: len(re.findall(t, txt)) for t in terms}
    print(f, 'FORBIDDEN TOTAL:', sum(c.values()), c)"
```

| Forbidden Pattern | `index.html` | `how_it_works.html` | `technical_catalog.html` | Total |
| :--- | :---: | :---: | :---: | :---: |
| `500M` | `0` | `0` | `0` | **`0`** |
| `3.03B` | `0` | `0` | `0` | **`0`** |
| `CLINICAL+` | `0` | `0` | `0` | **`0`** |
| `PHASE 4` | `0` | `0` | `0` | **`0`** |
| `GOLD` | `0` | `0` | `0` | **`0`** |
| `2.42M` | `0` | `0` | `0` | **`0`** |
| `99.8%` | `0` | `0` | `0` | **`0`** |
| `98.2%` | `0` | `0` | `0` | **`0`** |
| `280%` | `0` | `0` | `0` | **`0`** |
| `0.982` | `0` | `0` | `0` | **`0`** |
| `VERIFIED SAFE` | `0` | `0` | `0` | **`0`** |
| `attention heads` | `0` | `0` | `0` | **`0`** |
| `Transformer` | `0` | `0` | `0` | **`0`** |
| `CERTIFIED` | `0` | `0` | `0` | **`0`** |
| **Total Forbidden Matches** | **`0`** | **`0`** | **`0`** | **`0`** |

---

## 2. Screening Pipeline Output After Removing Hardcodes (Step 2.1)

### 2.1 Hardcoded Constants Removed (`Commit fd75d72`)
1. **`run_zenith_screening_pipeline.py:107–108` (`+1.65` synergy bonus) & `lines 276–328` (pitch-deck post-evaluation override block):**
   - Deleted `if has_sirt1 and has_sirt6 and has_zbtb16 and has_gata4: rejuv_multiplier += 1.65` (`line 107`) and deleted the post-evaluation override block (`if "NL-101" in name: delta_age = 13.00; esi = 0.928; ...`, `lines 276–328`) that forcibly overwrote `aging_engine` and `safety_engine` outputs for curated benchmarks.
2. **`services/bit_age_clock.py:24–149` (hand-set thresholds, weights, and `0.982` accuracy claim):**
   - Deleted `binarization_thresholds` (`15` hand-typed floats), `bit_weights` (`15` hand-typed regression weights), `_synthesize_expression`, and `"theoretical_accuracy_r": 0.982`. `binarize_expression()` and `calculate_age()` now raise an explicit `RuntimeError` stating that no calibrated biological clock checkpoint exists on the 14-donor discovery cohort (`LODO r = 0.351, p = 0.219`).
3. **`services/neuros_substrate_service.py:119–125` (`HEALTHY_BASELINES` & silent fallback):**
   - Deleted `HEALTHY_BASELINES` (`SCN5A: 4.2, GJA1: 5.1, ...`) and removed the silent fallback at `lines 221–223`. `encode_ion_profile()` now raises an explicit `ValueError` if `expression_vector` contains no positive resolved channel expression values.

### 2.2 What `NL-101` Scores Without the `+1.65` Bonus and Overrides
Command executed:
```bash
python run_zenith_screening_pipeline.py
```

Output summary (`zenith_screening_run.log` & `zenith_screening_audit.csv`):
```text
=====================================================================================
  DISCOVERY FUNNEL CONVERGENCE SUMMARY
=====================================================================================
  Stage 1 | Total Evaluated In Silico Combinations           : 516
  Stage 2 | Filtered by Primary Rejuvenation Gate (DeltaAge >= 5.0y) : 9 (1.7%)
  Stage 3 | Passed Electrical Conduction Gate (ESI >= 0.90)   : 141 (27.3%)
  Stage 4 | Passed Conformal Oncogenic Gate (CRC alpha=0.01) : 514 (99.6%)
  Stage 5 | Passed Strict Dual-Gate (DeltaAge >= 10y + ESI >= 0.90): 0 (0.0%)
  Stage 6 | Non-Dominated Pareto Frontier Set                : 0 cocktail(s)
-------------------------------------------------------------------------------------

=====================================================================================
  TOP 5 ALGORITHMICALLY RANKED CANDIDATES
=====================================================================================
Rank  | Cocktail Name                | Factors                      | DeltaAge  | ESI    | Status
-------------------------------------------------------------------------------------
1     | NL-101 (Zenith Lead)         | SIRT1+SIRT6+GATA4+ZBTB16     | -9.3  yr | 0.948  | ELIMINATED
2     | Zenith-Comb-0392             | SIRT1+SIRT6+GATA4+PPARGC1A   | -5.8  yr | 0.948  | ELIMINATED
3     | Ablation: dZBTB16            | SIRT1+SIRT6+GATA4            | -5.0  yr | 0.948  | ELIMINATED
4     | Zenith-Comb-0312             | SIRT1+SIRT6+GATA4+TET2       | -5.0  yr | 0.948  | ELIMINATED
5     | Zenith-Comb-0330             | SIRT1+SIRT6+GATA4+NKX2-5     | -5.0  yr | 0.948  | ELIMINATED

=====================================================================================
  DILIGENCE VERDICT
  0 candidates passed the strict dual gate (DeltaAge >= 10.0y + ESI >= 0.90).
  Top-ranked candidate NL-101 (Zenith Lead) (SIRT1+SIRT6+GATA4+ZBTB16) scored DeltaAge = -9.27 yr (< 10.0y threshold), ESI = 0.948.
=====================================================================================
```

- **Post-removal `NL-101` score:** `DeltaAge = -9.27 yr` (displayed as `-9.3 yr`), `ESI = 0.948`, `Status = ELIMINATED`.
- **Does any candidate pass the dual gate (`DeltaAge >= 10.0y + ESI >= 0.90`)?** **No (`0` of `516` cocktails, `0.0%`).** Without the hardcoded `+1.65` multiplier bonus and `delta_age = 13.00` override, `NL-101` remains Rank #1 by composite fitness (`-9.27 yr` vs `-5.82 yr` for Rank #2 `SIRT1+SIRT6+GATA4+PPARGC1A`), but falls `0.73 yr` short of the `10.0 yr` primary rejuvenation gate.

---

## 3. Ion Channel Panel Cell-Type Gating (Step 2.2 — `Commit 1fa73c0`)

In `perturbation_engine.py:497–554` and `bridge_server.py:7664–7725`:
- **Non-cardiomyocyte queries (`fibroblast`, `endothelial`, `macrophage`, `pericyte`, `smooth_muscle`, etc.):** The engine now explicitly declines to run the cardiac ion-channel conduction panel and returns:
  - `classification = "NOT_APPLICABLE_NON_CM"`
  - `reason = "Cardiac ion-channel conduction panel is restricted to excitable cardiomyocyte lineages; declined for non-cardiomyocyte source_type='fibroblast' (Fibroblast)."`
  - `phi_hat = None`, `synchrony = None`
- **Cardiomyocyte queries (`Ventricular_Myocyte`, `Atrial_Myocyte`, `Cardiomyocyte`):** The engine computes ion-channel expression directly from the scVI generative decoder (`float(predicted_expr[idx]) * 1000.0`, without `HEALTHY_BASELINES`) and evaluates `svc.substrate.audit_arrhythmia_risk(ion_expr)`.

Verification command and output:
```text
FIBROBLAST: NOT_APPLICABLE_NON_CM | Cardiac ion-channel conduction panel is restricted to excitable cardiomyocyte lineages; declined for non-cardiomyocyte source_type='fibroblast' (Fibroblast).
VCM: BLOCKED | phi_hat= 0.172398020275899 | sync= 0.0008993382095123242
```

---

## 4. The Four Commit SHAs & Git Status (Steps 3 & 4)

### 4.1 `git log -n 5 --oneline`
```text
1fa73c0 fix(ion-panel): gate cardiac conduction audit by cardiomyocyte lineage and compute expression from scVI decoding
fd75d72 fix(hardcodes): remove NL-101 +1.65 bonus and pitch-deck overrides, hand-set BiT Age weights/0.982, and HEALTHY_BASELINES
031f660 fix(arch): reconcile scVI specialist (20d, 99,993 trained cells, 3,268,462 trainable params) and foundation (4x1024x64) specs per audit_questions_answered.md
664b399 fix(html): remove unverified GOLD, Phase 4, 500M, Transformer, 2.42M, and 98.2%/99.8% claims per audit_questions_answered.md
66edf8e fix(simulation): align drift tensor dimensions to 5858 in simulate_step
```

| Commit Order | Commit SHA | Scope & Description |
| :---: | :---: | :--- |
| **Commit 1** | `664b399` | **HTML claim corrections:** Removed all occurrences of `500M`, `3.03B`, `CLINICAL+`, `PHASE 4`, `GOLD`, `2.42M`, `99.8%`, `98.2%`, `280%`, `0.982`, `VERIFIED SAFE`, `attention heads`, `Transformer`, `CERTIFIED` across `index.html`, `how_it_works.html`, and `technical_catalog.html`. |
| **Commit 2** | `031f660` | **Architecture figure corrections:** Reconciled Specialist (`2` layers × `128` channels × `20` latent, `99,993` trained cells [`89,994` train + `9,999` val] from `486,134`-cell source atlas, `3,268,462` trainable float params / `3,269,747` total tensor elements) and Foundation (`4` layers × `1,024` channels × `64` latent, `1,962,128` registered cells, `37,234,698` trainable float params). |
| **Commit 3** | `fd75d72` | **Hardcode removals:** Removed `NL-101` `+1.65` bonus and `276–328` pitch-deck overrides from `run_zenith_screening_pipeline.py`, hand-set weights/`0.982` from `services/bit_age_clock.py`, and `HEALTHY_BASELINES` from `services/neuros_substrate_service.py`. |
| **Commit 4** | `1fa73c0` | **Ion panel cell-type gating:** Restricted cardiac ion-channel conduction audit in `perturbation_engine.py` and `bridge_server.py` to cardiomyocyte lineages (`NOT_APPLICABLE_NON_CM` for fibroblasts/non-CMs) and decoded cardiomyocyte channel expression directly from scVI. |

### 4.2 `git status -uno` (Tracked Working Tree Status)
```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit (use -u to show untracked files)
```

### 4.3 Deployment Architecture (`git push origin main`)
- **Remote Repository:** `https://github.com/alaaaldeen1994/is-chrp-v26-zenith.git` (`main -> main`, pushed to `1fa73c0`).
- **Live Hosting Service:** **Railway (`railway-hikari`)** watches `origin/main` via `railway.json` (`builder: DOCKERFILE`, `dockerfilePath: Dockerfile`, `startCommand: uvicorn bridge_server:app --host 0.0.0.0 --port $PORT`). Pushing `1fa73c0` automatically triggered a container rebuild and live cutover at `19:17:05 GMT`.

---

## 5. Live HTTP Grep Table (`https://niluslab.com/` — Step 5)

### 5.1 Live HTTP Headers (`Before` vs `After` Deploy)

| Live URL | Pre-Deploy (`66edf8e`) `Last-Modified` & `ETag` | Post-Deploy (`1fa73c0`) `Last-Modified` & `ETag` | HTTP Status |
| :--- | :--- | :--- | :---: |
| `https://niluslab.com/index.html` | `Tue, 22 Sep 2026 10:55:18 GMT` / `"460708b96879bd490271700feb5866ff"` | **`Tue, 22 Sep 2026 19:17:05 GMT`** / **`"01df6c00b0d99172e17886ed056ec79b"`** | **`200 OK`** |
| `https://niluslab.com/how_it_works.html` | `Tue, 22 Sep 2026 10:55:18 GMT` / `"2d9a184f821ea8d911a0a4dffcd47374"` | **`Tue, 22 Sep 2026 19:17:05 GMT`** / **`"1e660d8dc2bcf74ce007f38428610e09"`** | **`200 OK`** |
| `https://niluslab.com/technical_catalog.html` | `Tue, 22 Sep 2026 10:55:18 GMT` / `"d66f3d0f586d90a71c6852a1c18cd3f2"` | **`Tue, 22 Sep 2026 19:17:05 GMT`** / **`"14fe749ca6e333ea5352d3b9c3712a7e"`** | **`200 OK`** |

### 5.2 Live Site Forbidden-String Grep Table (Fetched Over HTTP from `https://niluslab.com/`)

Command executed:
```bash
python -c "import urllib.request, re; urls = ['https://niluslab.com/index.html', 'https://niluslab.com/how_it_works.html', 'https://niluslab.com/technical_catalog.html']; terms = ['500M', '3.03B', 'CLINICAL\\+', 'PHASE 4', 'GOLD', '2\\.42M', '99\\.8%', '98\\.2%', '280%', '0\\.982', 'VERIFIED SAFE', 'attention heads', 'Transformer', 'CERTIFIED']; new_terms = ['99,993', '3,268,462', '3,269,747', '37,234,698', '1,962,128', '20-dimensional', '1,024'];
for u in urls:
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode('utf-8', errors='replace')
        counts = {t: len(re.findall(t, body)) for t in terms}
        new_counts = {t: len(re.findall(t, body)) for t in new_terms}
        print(u, 'FORBIDDEN TOTAL:', sum(counts.values()), counts, 'CORRECTED:', new_counts)"
```

| Forbidden Pattern | Live `index.html` (Pre $\rightarrow$ **Post**) | Live `how_it_works.html` (Pre $\rightarrow$ **Post**) | Live `technical_catalog.html` (Pre $\rightarrow$ **Post**) | Live Post-Deploy Total |
| :--- | :---: | :---: | :---: | :---: |
| `500M` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `23` $\rightarrow$ **`0`** | **`0`** |
| `3.03B` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | **`0`** |
| `CLINICAL+` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `1` $\rightarrow$ **`0`** | **`0`** |
| `PHASE 4` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `2` $\rightarrow$ **`0`** | **`0`** |
| `GOLD` | `2` $\rightarrow$ **`0`** | `3` $\rightarrow$ **`0`** | `40` $\rightarrow$ **`0`** | **`0`** |
| `2.42M` | `8` $\rightarrow$ **`0`** | `1` $\rightarrow$ **`0`** | `2` $\rightarrow$ **`0`** | **`0`** |
| `99.8%` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `2` $\rightarrow$ **`0`** | **`0`** |
| `98.2%` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `1` $\rightarrow$ **`0`** | **`0`** |
| `280%` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `1` $\rightarrow$ **`0`** | **`0`** |
| `0.982` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | **`0`** |
| `VERIFIED SAFE` | `1` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | **`0`** |
| `attention heads` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | **`0`** |
| `Transformer` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `7` $\rightarrow$ **`0`** | **`0`** |
| `CERTIFIED` | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | `0` $\rightarrow$ **`0`** | **`0`** |
| **Total Forbidden Matches** | `11` $\rightarrow$ **`0`** | `4` $\rightarrow$ **`0`** | `79` $\rightarrow$ **`0`** | **`0`** |

### 5.3 Live Site Corrected-Value Grep Table (Fetched Over HTTP from `https://niluslab.com/`)

| Corrected Value | Live `index.html` | Live `how_it_works.html` | Live `technical_catalog.html` | Live Post-Deploy Total |
| :--- | :---: | :---: | :---: | :---: |
| `99,993` (Trained Specialist cells) | **`4`** | **`1`** | **`5`** | **`10`** |
| `3,268,462` (Trainable Specialist float params) | **`1`** | **`1`** | **`9`** | **`11`** |
| `3,269,747` (Total Specialist tensor elements footnote) | **`1`** | **`1`** | **`6`** | **`8`** |
| `37,234,698` (Trainable Foundation float params) | **`0`** | **`0`** | **`5`** | **`5`** |
| `1,962,128` (Registered Foundation cells) | **`0`** | **`0`** | **`3`** | **`3`** |
| `20-dimensional` (Specialist latent space) | **`0`** | **`0`** | **`2`** | **`2`** |
| `1,024` (Foundation hidden channels) | **`0`** | **`0`** | **`2`** | **`2`** |

---

## 6. Three Document Corrections Applied (Step 6)

1. **6.1 Age Correlation Reversal & Sign Disambiguation (`replication.md` & `zenith_full_audit_response.md`):**
   - Corrected the Sanger vs. Harvard age description in `replication.md` (`Sections 2.1, 2.2, 6.1`) and `zenith_full_audit_response.md` (`Part 2.1`): in the 14-donor Litviňuková et al. (2020) cohort, **Sanger donors (`D1–D7`, $n=7$, whole cells, `10x 3' v2`) are older (`mean 60.0 yr`, range `50–75 yr`, midpoints `52.5–72.5 yr`)**, whereas **Harvard donors (`H2–H7`, $n=6$, single nuclei, `10x 3' v3`) are younger (`mean 48.2 yr`, range `40–60 yr`, midpoints `42.5–57.5 yr`)**.
   - Explicitly documented that $r_{\text{youth}} = \text{corr}(\text{expr}, -\text{age}) = -\text{corr}(\text{expr}, \text{age})$ and renamed all `"Up with Age"` / `"Down with Age"` table labels to **`"Up in Youth (Down with Age)"`** ($r_{\text{youth}} > 0$) and **`"Down in Youth (Up with Age)"`** ($r_{\text{youth}} < 0$).
2. **6.2 Part 5 Heading & First Sentence (`replication.md` & `zenith_full_audit_response.md`):**
   - Replaced `"## Part 5 — Genes That DO Replicate Across Cohorts"` with:
     ```markdown
     ## Part 5 — Genes Exceeding |r| >= 0.30 in Both Cohorts (Not Enriched Above Chance)

     Of 5,262 shared genes, 152 (2.89%) exceed |r| >= 0.30 in both cohorts with the same sign, versus 189 (3.59%) with the opposite sign — below the 50% random expectation.
     ```
3. **6.3 Removal of Self-Certification & Hardcode/Ion-Panel Updates (`zenith_full_audit_response.md`):**
   - Removed `"Independent Assessment"` (`line 2`) and `"Certified under Zenith Remediation Protocol"` (`line 199`).
   - Updated the `"zero hardcodes"` claim (`Part 2.4` and `Part 4`) to document the four hardcoded blocks that remained until `Commit fd75d72`.
   - Replaced `"0.942"` (`Part 2.3`) with the actual `audit_arrhythmia_risk` output keys (`phi_hat = 0.008892`, `synchrony = 0.033421`, `isi_variance = 495.5399` under baseline, and `NOT_APPLICABLE_NON_CM` for non-cardiomyocyte queries after `Commit 1fa73c0`).

---

## 7. Centred Sign-Concordance Diagnostic (Step 7)

Command executed:
```bash
python -c "import pickle, numpy as np; from scipy.stats import pearsonr
d = pickle.load(open('scratch/phaseE_pseudobulk_cache.pkl', 'rb'))
for name, k1, k2 in [('Fibroblast', 'lit_fib', 'peri_fib'), ('vCM -> Atrial CM', 'lit_vcm', 'peri_acm'), ('Atrial CM -> Atrial CM', 'lit_acm', 'peri_acm')]:
    g1, g2 = d[k1]['r'], d[k2]['r']
    shared = sorted(set(g1.keys()) & set(g2.keys()))
    r1 = np.array([g1[g] for g in shared])
    r2 = np.array([g2[g] for g in shared])
    r1_c, r2_c = r1 - np.mean(r1), r2 - np.mean(r2)
    raw_conc = np.mean(np.sign(r1) == np.sign(r2)) * 100
    cen_conc = np.mean(np.sign(r1_c) == np.sign(r2_c)) * 100
    pr, pp = pearsonr(r1, r2)
    print(f'{name} (n={len(shared)}): mean1={np.mean(r1):+.4f} ({np.mean(r1>0)*100:.2f}% >0), mean2={np.mean(r2):+.4f} ({np.mean(r2>0)*100:.2f}% >0) | Pearson r={pr:+.4f} (p={pp:.2e}) | Raw Sign Conc={raw_conc:.2f}% -> Centred Sign Conc={cen_conc:.2f}%')"
```

| Cell-Type Comparison | Shared Active Genes ($n$) | Cohort 1 Mean $r_{\text{youth}}$ (% Positive) | Cohort 2 Mean $r_{\text{youth}}$ (% Positive) | Genome-Wide Pearson $r$ ($p$-value) | Raw Sign Concordance | **Centred Sign Concordance (`r - mean(r)`)** | Median-Centred Sign Concordance | Theoretical $\frac{1}{2} + \frac{1}{\pi}\arcsin(r)$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fibroblast** (Lit14 vs Peri54) | `5,262` | `$+0.3337$` (`78.20%`) | `$+0.0833$` (`68.53%`) | **`$-0.4161$`** ($1.96 \times 10^{-219}$) | `52.28%` | **`36.89%`** | `38.62%` | `36.34%` |
| **vCM $\rightarrow$ Atrial CM** | `6,717` | `$+0.2851$` (`76.30%`) | `$+0.0765$` (`65.40%`) | **`$-0.1868$`** ($8.20 \times 10^{-54}$) | `54.62%` | **`45.96%`** | `46.24%` | `44.02%` |
| **Atrial CM $\rightarrow$ Atrial CM** | `6,768` | `$+0.1969$` (`70.60%`) | `$+0.0780$` (`65.62%`) | **`$-0.2296$`** ($1.07 \times 10^{-81}$) | `51.82%` | **`43.03%`** | `43.23%` | `42.63%` |

**Interpretation:** Subtracting each cohort's global mean offset (`+0.3337` in Litviňuková fibroblasts, where `78.20%` of active genes correlate positively with youthfulness due to higher transcript complexity in younger Harvard nuclei vs. older Sanger cells, and `+0.0833` in PERIHEART fibroblasts, where `68.53%` are positive) drops fibroblast sign concordance from **`52.28%`** to **`36.89%`**, matching the theoretical Sheppard's theorem prediction (`36.34%`) for $r = -0.4161$. This confirms that raw sign concordance exceeded 50% solely due to shared positive global mean offsets while gene-by-gene variation around the mean is anti-correlated across cohorts.

---

**Yes — the public site now serves the corrected build (`Commit 1fa73c0` live on `https://niluslab.com/` as of `Tue, 22 Sep 2026 19:17:05 GMT`), with `0` occurrences of all 13 forbidden claims (`500M`, `3.03B`, `CLINICAL+`, `PHASE 4`, `GOLD`, `2.42M`, `99.8%`, `98.2%`, `280%`, `0.982`, `VERIFIED SAFE`, `attention heads`, `Transformer`, `CERTIFIED`) across `index.html`, `how_it_works.html`, and `technical_catalog.html`.**
