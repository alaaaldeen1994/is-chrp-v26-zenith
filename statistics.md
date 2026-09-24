# Phase 4: Statistical Rigor, Donor-Level Pseudobulk ($n = 14$), Confounding & GRN Null Calibration

**Audit Date:** September 22, 2026  
**Repository:** `c:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative`  
**Verification Scripts:** [`scripts/run_phase3_and_phase4_validation.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/scripts/run_phase3_and_phase4_validation.py), [`scripts/run_phase4_4_grn.py`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scripts/run_phase4_4_grn.py)  
**Primary Data Artifacts:** [`scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv), [`scratch/phase3_4_fibroblast_correlations.csv`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase3_4_fibroblast_correlations.csv), [`scratch/phase4_donor_qc_confound.csv`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase4_donor_qc_confound.csv), [`scratch/phase4_4_grn_summary.json`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase4_4_grn_summary.json)

---

## Executive Summary: Primary Negative Findings (Reported First)

> [!CAUTION]
> **Summary of Negative & Null Findings Across Phases 4.1–4.4**
> Before presenting positive survival rates or GRN percentiles, four fundamental statistical and experimental limitations must be stated upfront:
>
> 1. **Severe Institution/Center Batch Confounding in the 14-Donor HCA Cohort ($r_{\text{age, center}} = +0.779, p = 0.0010$):**
>    In `Litviňuková et al. (Nature 2020)`, the 14 adult heart donors come from two processing centers: **Harvard (`H2–H7`, `Harvard-Nuclei`, $n=6$)** and **Wellcome Sanger Institute (`D1–D7, D11`, `Sanger-Nuclei`, $n=8$)**. **100% of the Harvard donors (`H2–H7`) are $< 60\text{ years old}$ (`42.5–57.5y`, mean `50.8y`)**, whereas **7 of the 8 Sanger donors (`D2–D11`) are $57.5\text{–}72.5\text{ years old}$ (mean `63.8y`)**, and **100% of donors $\ge 65\text{y}$ (`D4, D5, D6`) were processed at Sanger**. Consequently, chronological age and processing center are collinear ($r = +0.779$).
> 2. **Top Table Markers (`HSPB1`, `CRYAB`, `TTN-AS1`) Lose Age Significance After Adjusting for Processing Center & UMI Depth:**
>    - **`HSPB1`** (#1 aging marker in vCM table, `r_json = -0.4182`; unadjusted donor $r_{\text{age}} = +0.6969, p = 0.0056$) correlates more strongly with `Sanger vs Harvard` center ($r_{\text{site}} = +0.7154, p = 0.0040$). In an OLS regression adjusting for processing center and median UMI depth ($n = 14$), **`HSPB1`'s age coefficient becomes statistically non-significant ($\beta_{\text{age}} = +0.0329, t = +1.21, p = 0.2553$)**.
>    - **`CRYAB`** (#3 aging marker in vCM table, `r_json = -0.3522`; unadjusted donor $r_{\text{age}} = +0.7557, p = 0.0018$) correlates more strongly with `Sanger vs Harvard` center ($r_{\text{site}} = +0.7638, p = 0.0015$) and UMI depth ($r_{\text{UMI}} = +0.5467, p = 0.0431$). Adjusting for center and UMI depth, **`CRYAB`'s age coefficient becomes statistically non-significant ($\beta_{\text{age}} = +0.0291, t = +1.57, p = 0.1486$)**.
>    - **`TTN-AS1`** (#1 pro-rejuvenation marker in vCM table, `r_json = +0.3002`; unadjusted donor $r_{\text{age}} = -0.5809, p = 0.0294$) is overwhelmingly a center batch marker ($r_{\text{site}} = -0.8764, p = 0.00004$). Adjusting for center and UMI depth, **`TTN-AS1`'s age effect vanishes completely and flips sign ($\beta_{\text{age}} = +0.0136, t = +0.64, p = 0.5356$), while the center batch effect remains highly significant ($\beta_{\text{site}} = -1.9050, t = -4.99, p = 0.0005$)**.
> 3. **6-Fold Inflated False-Positive Rate Among Random Genes at $n = 14$ Donors (`28.6%` Reach $p < 0.05$):**
>    When **500 randomly selected cardiac genes** matched for detection frequency (`5%–95%` of vCMs) are correlated against donor chronological age across the 14 donors, **`143 / 500` (`28.6%`, vs `5.0%` expected under a well-calibrated null) reach nominal $p < 0.05$**, and **`10 / 500` (`2.0%`) survive Benjamini–Hochberg $q < 0.05$**. The 95th percentile of $|r|$ for random genes is **`0.7230`** (`90th = 0.6747`, `50th = 0.3785`), because any gene with an institutional expression offset between Harvard and Sanger automatically correlates with donor age. Only **`7 / 100`** genes in the vCM table exceed the 95th percentile (`|r| > 0.7230`) of random frequency-matched genes.
> 4. **GRN Perturbation Screen Out-Degree Bias ($R^2 = 0.4656$ in Positive Single TFs; $R^2 = 0.4579$ Across 211 Quads):**
>    In our 3-step linear Ridge GRN screen (`screen_output.csv`), $\log_{10}(\text{out-degree})$ explains **$46.56\%$ of the variance ($r = +0.6823, p = 2.13 \times 10^{-23}$)** among positive single TFs ($n = 161$) and **$45.79\%$ of the variance ($r = +0.6767, p = 1.32 \times 10^{-29}$)** across all 211 evaluated 4-TF combinations. When $\log_{10}(\text{total edges})$ is regressed out across the 211 quads, the raw #1 combination **`NFKB1+MITF+CTCF+HIF1A` (`+6.0693%`, `2,652` base edges) drops to Rank #2 (`residual = +1.3406%`)**, overtaken by **`NFKB1+MITF+HIF1A+NFIC` (Rank #1, `residual = +1.3780%`, raw `+5.5736%`, `2,075` base edges)**. Moreover, **2 combinations (`NFKB1+MITF+CTCF+HIF1A` and `NFKB1+MITF+HIF1A+REL`) fall inside the winner's 95% donor-bootstrap CI (`[+5.765%, +6.249%]`)**, and the top 10 quads are separated by only `0.61` percentage points (`+5.4595%` to `+6.0693%`).

---

## 4.1 Donor-Level Pseudobulk Re-Analysis ($n = 14$ Independent Biological Replicates)

In `models/cell_type_genes.json`, correlations were computed across $N_c = 125,289$ individual ventricular cardiomyocytes or $N_c = 59,341$ fibroblasts. Because cells from the same human heart share donor genetics, medical history, post-mortem ischemia time, and processing center, the effective sample size for chronological aging inference is **$n = 14$ donors (`df = 12`)**, where the critical threshold for two-sided $p < 0.05$ is $|r| > 0.5324$.

### Summary of Donor-Level Survival ($n = 14$, `df = 12`)

| Cell Type | Total Table Genes | Same Sign as `r_json` | Nominal $p < 0.05$ ($|r| > 0.5324$ at $n=14$) | Benjamini–Hochberg FDR $q < 0.05$ | Exceeds 95th Percentile of 500 Random Genes ($|r| > 0.7230$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Ventricular Cardiomyocyte (`vCM`)** | `100` | `100 / 100` (`100%`) | **`63 / 100` (`63.0%`)** | **`48 / 100` (`48.0%`)** | **`7 / 100` (`7.0%`)** |
| **Fibroblast** | `100` | `100 / 100` (`100%`) | **`80 / 100` (`80.0%`)** | **`74 / 100` (`74.0%`)** | **`18 / 100` (`18.0%`)** |

### Top 18 Ventricular Cardiomyocyte (`vCM`) Table Genes — Cell-Level vs Donor-Level ($n = 14$)

*(Full 100-gene table saved in [`scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv); positive $r$ = youth-associated, negative $r$ = aged-associated)*

| Gene Symbol | `r_json` (`125,289` cells, Colab) | `r_local_scvi_proj` (`5,307` cells) | `r_local_cell_youth` (`5,307` cells) | `r_donor_youth` ($n = 14$ donor means) | 95% Fisher $z$ CI ($n = 14$) | Two-Sided $p$-Value ($n = 14$) | BH-Adjusted $q$-Value | Survives BH $q < 0.05$? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`HSPB1`** | `-0.4182` | `-0.5339` | `-0.4799` | **`-0.6969`** | `[-0.896, -0.264]` | `0.0056` | `0.0330` | Yes *(Site-confounded)* |
| **`LINGO1`** | `-0.4141` | `-0.5808` | `-0.5321` | **`-0.7152`** | `[-0.903, -0.297]` | `0.0040` | `0.0330` | Yes |
| **`CRYAB`** | `-0.3522` | `-0.3873` | `-0.3830` | **`-0.7557`** | `[-0.918, -0.376]` | `0.0018` | `0.0330` | Yes *(Site-confounded)* |
| **`MALAT1`** | `-0.3424` | `-0.5841` | `-0.4396` | **`-0.5730`** | `[-0.846, -0.061]` | `0.0322` | `0.0613` | **No** ($q = 0.061$) |
| **`ANKRD1`** | `-0.3396` | `-0.3404` | `-0.1653` | **`-0.5091`** | `[-0.819, +0.029]` | `0.0630` | `0.0919` | **No** ($p = 0.063$) |
| **`DUSP1`** | `-0.3115` | `-0.4289` | `-0.3678` | **`-0.7684`** | `[-0.923, -0.402]` | `0.0013` | `0.0330` | Yes |
| **`MYL2`** | `-0.3077` | `-0.2797` | `-0.2190` | **`-0.4885`** | `[-0.809, +0.057]` | `0.0763` | `0.1032` | **No** ($p = 0.076$) |
| **`TTN-AS1`** | `+0.3002` | `+0.4981` | `+0.4310` | **`+0.5809`** | `[+0.073, +0.850]` | `0.0294` | `0.0588` | **No** ($q = 0.059$; Site-driven) |
| **`APOD`** | `-0.2882` | `-0.2711` | `-0.3250` | **`-0.5486`** | `[-0.836, -0.025]` | `0.0422` | `0.0704` | **No** ($q = 0.070$) |
| **`ACTC1`** | `-0.2735` | `-0.2809` | `-0.3033` | **`-0.6873`** | `[-0.892, -0.247]` | `0.0066` | `0.0330` | Yes |
| **`NR4A3`** | `-0.2657` | `-0.4223` | `-0.3435` | **`-0.7241`** | `[-0.906, -0.314]` | `0.0034` | `0.0330` | Yes |
| **`PDK4`** | `-0.2607` | `-0.4499` | `-0.1282` | **`-0.1626`** | `[-0.638, +0.403]` | `0.5787` | `0.6092` | **No** ($p = 0.579$) |
| **`SPDYE2`** | `-0.2474` | `-0.3606` | `-0.3300` | **`-0.6619`** | `[-0.883, -0.202]` | `0.0099` | `0.0330` | Yes |
| **`MLIP-AS1`** | `+0.2446` | `+0.4354` | `+0.3537` | **`+0.6041`** | `[+0.108, +0.859]` | `0.0222` | `0.0461` | Yes |
| **`SLC26A3`** | `-0.2380` | `-0.3389` | `-0.3199` | **`-0.6508`** | `[-0.878, -0.184]` | `0.0117` | `0.0357` | Yes |
| **`CCN1`** | `-0.2290` | `-0.3176` | `-0.1612` | **`-0.5785`** | `[-0.849, -0.069]` | `0.0302` | `0.0593` | **No** ($q = 0.059$) |
| **`PPP1R3C`** | `-0.2266` | `-0.3758` | `-0.3714` | **`-0.7641`** | `[-0.921, -0.393]` | `0.0015` | `0.0330` | Yes |
| **`PDLIM3`** | `-0.2228` | `-0.2913` | `-0.2393` | **`-0.6162`** | `[-0.864, -0.127]` | `0.0189` | `0.0430` | Yes |

---

## 4.2 Dissociation Stress & Institutional Batch Confound (`HSPB1`, `CRYAB`, `TTN-AS1`)

The two strongest negative correlations in the vCM table (`HSPB1`, $r_{\text{json}} = -0.4182$, and `CRYAB`, $r_{\text{json}} = -0.3522$) encode canonical small heat-shock proteins (Hsp27 and $\alpha$B-crystallin), and the third (`DUSP1`, $r_{\text{json}} = -0.3115$) and eleventh (`NR4A3`, $r_{\text{json}} = -0.2657$) are immediate-early stress-response genes induced by warm enzymatic/mechanical tissue handling and post-mortem ischemia.

To test whether `HSPB1`, `CRYAB`, and the #1 pro-rejuvenation marker `TTN-AS1` reflect true biological aging or institutional/technical differences across the 14 donors, we cross-tabulated all 14 donors (`scratch/phase4_donor_qc_confound.csv`):

### 14-Donor Metadata, Sequencing QC, and Marker Expression (`vCM` Subset, $n = 5,307$)

| Donor ID | Age Midpoint (yr) | Age Bracket (`extract_celltype_genes.py`) | Processing Center (`cell_source`) | Sex | `n_vcms` (Local) | Median UMI / Cell | Median Genes / Cell | Median `% Mito` | `HSPB1` Mean ($\log\text{CP10k}$) | `CRYAB` Mean ($\log\text{CP10k}$) | `TTN-AS1` Mean ($\log\text{CP10k}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **H6** | `42.5` | `young_le55` | `Harvard-Nuclei` | Female | `539` | `3,963.0` | `1,773.0` | `0.094%` | `0.2927` | `0.8898` | `2.6580` |
| **H7** | `47.5` | `young_le55` | `Harvard-Nuclei` | Female | `433` | `3,091.0` | `1,494.0` | `0.069%` | `0.1102` | `0.8223` | `2.7621` |
| **H2** | `52.5` | `young_le55` | `Harvard-Nuclei` | Male | `228` | `3,258.0` | `1,599.5` | `0.051%` | `0.1827` | `0.8465` | `2.7082` |
| **H3** | `52.5` | `young_le55` | `Harvard-Nuclei` | Male | `418` | `3,518.0` | `1,677.0` | `0.082%` | `0.0483` | `0.7759` | `2.7634` |
| **H5** | `52.5` | `young_le55` | `Harvard-Nuclei` | Female | `814` | `3,380.5` | `1,606.5` | `0.080%` | `0.1068` | `0.7262` | `2.6811` |
| **D1** | `52.5` | `young_le55` | `Sanger-Nuclei` | Female | `326` | `3,471.0` | `1,357.0` | `0.035%` | **`1.0168`** | **`1.4503`** | **`0.8824`** |
| **H4** | `57.5` | `middle_57_62` | `Harvard-Nuclei` | Male | `440` | `3,241.5` | `1,521.0` | `0.087%` | `0.1432` | `0.8232` | `2.6715` |
| **D3** | `57.5` | `middle_57_62` | `Sanger-Nuclei` | Male | `212` | `3,560.0` | `1,368.5` | `0.076%` | **`0.7401`** | **`1.3222`** | **`1.1190`** |
| **D2** | `62.5` | `middle_57_62` | `Sanger-Nuclei` | Male | `539` | `3,694.0` | `1,447.0` | `0.061%` | **`1.1001`** | **`1.3263`** | **`0.9961`** |
| **D7** | `62.5` | `middle_57_62` | `Sanger-Nuclei` | Male | `252` | `3,718.5` | `1,602.5` | `0.050%` | **`2.0368`** | **`2.2803`** | **`1.2015`** |
| **D11** | `62.5` | `middle_57_62` | `Sanger-Nuclei` | Female | `199` | `4,939.0` | `1,751.0` | `0.056%` | `0.2229` | **`1.6472`** | **`0.4608`** |
| **D5** | `67.5` | `aged_ge65` | `Sanger-Nuclei` | Female | `371` | `3,133.0` | `1,285.0` | `0.046%` | **`1.1764`** | **`1.7178`** | **`1.0504`** |
| **D4** | `72.5` | `aged_ge65` | `Sanger-Nuclei` | Female | `321` | `3,818.0` | `1,530.0` | `0.033%` | **`1.0889`** | **`1.5733`** | **`0.7712`** |
| **D6** | `72.5` | `aged_ge65` | `Sanger-Nuclei` | Male | `215` | `4,457.0` | `1,799.0` | `0.152%` | **`2.6331`** | **`2.9938`** | **`1.1444`** |

> [!WARNING]
> **Look at Age-Matched Donors `D1` (`52.5y`, `Sanger-Nuclei`) vs `H2, H3, H5` (`52.5y`, `Harvard-Nuclei`) and `D3` (`57.5y`, `Sanger-Nuclei`) vs `H4` (`57.5y`, `Harvard-Nuclei`):**
> - At the **exact same chronological age (`52.5y`)**, Sanger donor `D1` has **`HSPB1 = 1.0168`** and **`TTN-AS1 = 0.8824`**, whereas Harvard donors `H2, H3, H5` (`52.5y`) have **`HSPB1 = 0.0483–0.1827`** ($9\times$ lower!) and **`TTN-AS1 = 2.6811–2.7634`** ($3\times$ higher!).
> - At the **exact same chronological age (`57.5y`)**, Sanger donor `D3` has **`HSPB1 = 0.7401`** and **`TTN-AS1 = 1.1190`**, whereas Harvard donor `H4` (`57.5y`) has **`HSPB1 = 0.1432`** ($5\times$ lower!) and **`TTN-AS1 = 2.6715`** ($2.4\times$ higher!).

### Unadjusted vs Center-and-UMI-Adjusted OLS Regression ($n = 14$ Donors)

| Marker Gene | Unadjusted $r$ vs Chronological Age ($p$-value) | Unadjusted $r$ vs Center `Sanger_D` ($p$-value) | Unadjusted $r$ vs Median UMI ($p$-value) | OLS $\beta_{\text{age}}$ Adjusted for Center + UMI ($t$, $p$-value) | OLS $\beta_{\text{center\_D}}$ Adjusted for Age + UMI ($t$, $p$-value) | Survives Adjustment for Center + Depth? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`HSPB1`** | `+0.6969` (`p = 0.0056`) | **`+0.7154` (`p = 0.0040`)** | `+0.3153` (`p = 0.2722`) | **`+0.0329` (`t = +1.21`, `p = 0.2553`)** | `+0.6910` (`t = +1.40`, `p = 0.1903`) | **NO ($p = 0.255$)** |
| **`CRYAB`** | `+0.7557` (`p = 0.0018`) | **`+0.7638` (`p = 0.0015`)** | **`+0.5467` (`p = 0.0431`)** | **`+0.0291` (`t = +1.57`, `p = 0.1486`)** | `+0.4643` (`t = +1.38`, `p = 0.1962`) | **NO ($p = 0.149$)** |
| **`TTN-AS1`** | `-0.5809` (`p = 0.0294`) | **`-0.8764` (`p = 0.00004`)** | `-0.2164` (`p = 0.4575`) | **`+0.0136` (`t = +0.64`, `p = 0.5356`)** | **`-1.9050` (`t = -4.99`, `p = 0.0005`)** | **NO ($p = 0.536$; sign flips)** |

---

## 4.3 Empirical False-Positive Calibration (`500` Random Frequency-Matched Genes at $n = 14$)

To determine the empirical null distribution of donor-level correlations in this 14-donor cohort, we drew **500 random cardiac genes** matched to the detection frequency range (`5%–95%` of vCMs) of the table genes (`seed = 42`) and computed their donor-level Pearson $|r|$ and two-sided $p$-value against chronological age across the 14 donors:

| Metric ($n = 14$ Donors) | Theoretical Unconfounded Null ($n = 14$, $\text{df} = 12$) | Empirical Random-Gene Null (`500` Frequency-Matched Genes in HCA Cohort) | `cell_type_genes.json` vCM Table (`100` Selected Genes) |
| :--- | :---: | :---: | :---: |
| **Proportion Reaching Nominal $p < 0.05$ ($|r| > 0.5324$)** | `5.0%` (`25 / 500`) | **`28.6%` (`143 / 500`)** ($5.7\times$ inflation) | **`63.0%` (`63 / 100`)** |
| **Proportion Surviving BH $q < 0.05$** | `0.0%` | **`2.0%` (`10 / 500`)** | **`48.0%` (`48 / 100`)** |
| **50th Percentile (Median) of Donor $|r|$** | `0.193` | **`0.3785`** | **`0.5797`** |
| **90th Percentile of Donor $|r|$** | `0.457` | **`0.6747`** | **`0.7062`** |
| **95th Percentile of Donor $|r|$** | `0.532` | **`0.7230`** | **`0.7411`** |
| **99th Percentile of Donor $|r|$** | `0.661` | **`0.7940`** | **`0.7684`** (Max in vCM table: `DUSP1`, $|r| = 0.7684$) |

**Interpretation:** Because donor chronological age is correlated at $r = +0.779$ with `Sanger vs Harvard` center, the median random gene in this dataset exhibits $|r| = 0.3785$ with donor age, and `28.6%` of random genes pass $p < 0.05$. While the 100 vCM table genes have a higher median $|r|$ (`0.5797` vs `0.3785`) because `extract_celltype_genes.py` explicitly selected the top 100 correlates of the `scVI` `young - aged` vector, **their 95th percentile (`0.7411`) is barely distinguishable from the 95th percentile of random genes (`0.7230`)**, and the maximum donor $|r|$ in the vCM table (`DUSP1`, `0.7684`) is below the 99th percentile of random genes (`0.7940`).

---

## 4.4 GRN Screen Null Distributions, Out-Degree Artifact Analysis, and Top-Quad Spread

In [`scripts/run_phase4_4_grn.py`](file:///c:/Users/alaaa\.gemini/antigravity/scratch/is-chrp-v26-generative/scripts/run_phase4_4_grn.py), we evaluated our Part 2 Ridge GRN perturbation model (`B_all`, `2,424` active vCM genes, `10,331` CollecTRI/DoRothEA interactions) against the three adversarial checks required by Phase 4.4:

### 4.4(a) Empirical Null Distributions: `1,000` Random 4-TF Sets vs `438` Degree-Matched 4-TF Sets

| Distribution ($n$ Combinations) | Mean Active Out-Degree (Edges) | Mean Youth Restoration (`%`) | Standard Deviation (`%`) | 5th Percentile (`%`) | 50th Percentile (`%`) | 95th Percentile (`%`) | Maximum Observed (`%`) | Positive (`> 0%`) / Negative (`< 0%`) | Winner (`NFKB1+MITF+CTCF+HIF1A`, `+6.0693%`) Percentile & Empirical $p$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random 4-TF Null** (`1,000` random quads from `238` TFs) | `204.9` | **`+0.0280%`** | `1.3252%` | `-1.9080%` | `+0.1672%` | **`+1.5549%`** | `+3.4594%` | `693` (`69.3%`) / `307` (`30.7%`) | **`100.00th pct` ($p < 0.001$)** |
| **Degree-Matched Hub 4-TF Null** (`438` unique hub quads with `1,553–2,035` active edges, matching winner's `1,828` active edges $\pm 15\%$) | `1,648.1` | **`-1.2546%`** | `3.9009%` | `-6.7614%` | `-1.5540%` | **`+4.7814%`** | `+5.7232%` | `193` (`44.1%`) / `245` (`55.9%`) | **`100.00th pct` ($p < 0.0023$)** |

**Why the Degree-Matched Null Has a Negative Mean (`-1.2546%`) and Wide Spread (`SD = 3.9009%`):**
- High-degree hub TFs (`SP1` with `779` edges, `TP53` with `634` edges, `MYC` with `612` edges, `RELA` with `568` edges, `STAT3` with `504` edges, `JUN` with `488` edges) drive large transcriptomic shifts in **both** directions. Because many stress/senescence hub TFs (`TP53`, `RELA`, `STAT3`, `JUN`) push cardiomyocytes *toward* the aged state (`-6.76%` at the 5th percentile), random combinations of 4 high-degree TFs average `-1.2546%` (`55.9%` negative).
- `NFKB1+MITF+CTCF+HIF1A` (`+6.0693%`, `1,828` active vCM edges / `2,652` total base edges) ranks at the `100.00th` percentile of both the random null (`max = +3.4594%`) and the degree-matched null (`max = +5.7232%`) because the Stage 1 funnel (`run_part2_real_screen.py`) specifically pre-selected the top 15 *positively directed* single TFs before forming pairs, triples, and quads.

### 4.4(b) Out-Degree Correlation & Residual Re-Ranking (`NFKB1+MITF+CTCF+HIF1A` Drops to Rank #2)

While random hub combinations can be positive or negative (`Pearson r = -0.0921` across all `238` single TFs when signed scores are pooled), **among positive-scoring TFs and evaluated Stage-3 quads, out-degree accounts for nearly half of the variance in the score:**

1. **Across All 238 Single TFs (`|Score|` Magnitude vs $\log_{10}(\text{Out-Degree})$):**
   $$r = +0.5350, \quad R^2 = 0.2862 \quad (p = 5.07 \times 10^{-19})$$
2. **Across Positive Single TFs ($n = 161$, `Score > 0` vs $\log_{10}(\text{Out-Degree})$):**
   $$r = +0.6823, \quad R^2 = 0.4656 \quad (p = 2.13 \times 10^{-23})$$
3. **Across All 211 Evaluated 4-TF Quads (`Score` vs $\log_{10}(\text{Total Base Edges})$):**
   $$r = +0.6767, \quad R^2 = 0.4579 \quad (p = 1.32 \times 10^{-29})$$

When we regress `youth_restoration_pct_excl` on $\log_{10}(\text{edges} + 1)$ across all 211 evaluated 4-TF quads and rank by the **degree-adjusted residual**, **`NFKB1+MITF+CTCF+HIF1A` does NOT hold Rank #1 — it drops to Rank #2**, overtaken by **`NFKB1+MITF+HIF1A+NFIC`**:

| Degree-Adjusted Residual Rank | Raw Score Rank | 4-TF Combination (`Stage3_Quads`) | Raw Youth Restoration (`%`) | Total Base GRN Edges (`CollecTRI/DoRothEA`) | Active vCM Edges (`2,424` genes) | Degree-Adjusted Residual (`%`) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **#1** | #7 | **`NFKB1+MITF+HIF1A+NFIC`** | `+5.5736%` | `2,075` | `1,445` | **`+1.3780%`** |
| **#2** | **#1** | **`NFKB1+MITF+CTCF+HIF1A`** *(Raw Winner)* | **`+6.0693%`** | **`2,652`** | **`1,828`** | **`+1.3406%`** |
| **#3** | #18 | **`MITF+CTCF+HIF1A+NFIC`** | `+5.2106%` | `1,794` | `1,250` | **`+1.3311%`** |
| **#4** | #6 | **`NFKB1+MITF+HIF1A+YY1`** | `+5.5966%` | `2,275` | `1,603` | **`+1.2010%`** |
| **#5** | #10 | **`NFKB1+MITF+CTCF+NFIC`** | `+5.4595%` | `2,214` | `1,540` | **`+1.1230%`** |
| **#6** | #42 | **`MITF+HIF1A+YY1+NFIC`** | `+4.4666%` | `1,417` | `992` | **`+1.0995%`** |

### 4.4(c) Overlap Within the Winner's 95% Bootstrap Confidence Interval (`[+5.765%, +6.249%]`)

Across the 211 evaluated 4-TF combinations in `screen_output.csv`, **2 combinations fall within the winner's 95% donor-bootstrap confidence interval (`[+5.765%, +6.249%]`)**, and the 3rd-ranked combination (`+5.7232%`) lies just `0.042%` below the lower bound:

| Raw Rank | 4-TF Combination | Youth Restoration Excl. (`%`) | Inside Winner's 95% CI (`[5.765%, 6.249%]`)? | `GJA1` Shift | `SCN5A` Shift | `ATP2A2` Shift |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | **`NFKB1+MITF+CTCF+HIF1A`** | **`+6.0693%`** | **YES** | `+0.01138` | `+0.08534` | `+0.03890` |
| **#2** | **`NFKB1+MITF+HIF1A+REL`** | **`+5.8436%`** | **YES** | `+0.00871` | `+0.04048` | `+0.04154` |
| **#3** | **`NFKB1+MITF+CTCF+REL`** | **`+5.7232%`** | Borderline (`-0.042%` from CI) | `+0.00854` | `+0.07456` | `+0.04656` |
| **#4** | **`NFKB1+MITF+HIF1A+JUND`** | **`+5.6037%`** | No (`95% CI` overlaps #2/#3) | `+0.00989` | `+0.03211` | `+0.03225` |
| **#5** | **`MITF+CTCF+HIF1A+REL`** | **`+5.5968%`** | No (`95% CI` overlaps #2/#3) | `+0.00848` | `+0.08136` | `+0.03514` |
| **#6** | **`NFKB1+MITF+HIF1A+YY1`** | **`+5.5966%`** | No (`95% CI` overlaps #2/#3) | `+0.00742` | `+0.05208` | `+0.03951` |
| **#7** | **`NFKB1+MITF+HIF1A+NFIC`** | **`+5.5736%`** | No (**#1 by degree residual**) | `+0.01120` | `+0.04463` | `+0.03418` |

**Conclusion on Section 4.4:** Because our linear 3-step Ridge GRN model has no non-linear epistasis (`propagate_perturbation` is strictly additive across clamped TFs except where target indices overlap), the top 10 quads are near-additive combinations of the same 4–6 high-out-degree TFs (`NFKB1`, `MITF`, `HIF1A`, `CTCF`, `REL`, `NFIC`). Consequently, **`NFKB1+MITF+CTCF+HIF1A` (`+6.0693%`) is statistically indistinguishable from `NFKB1+MITF+HIF1A+REL` (`+5.8436%`) within donor-bootstrap uncertainty, and ranks #2 behind `NFKB1+MITF+HIF1A+NFIC` after adjusting for GRN out-degree ($R^2 = 0.4579$).**
