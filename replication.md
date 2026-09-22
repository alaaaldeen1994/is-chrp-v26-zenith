# Zenith Platform — Phase E: Cross-Cohort Replication Report
## Independent Cross-Cohort Evaluation in the 54-Donor PERIHEART Atlas

**Document Status:** Final Verified Execution  
**Execution Date:** September 2026  
**Primary Question:** Do cellular aging signatures discovered in the 14-donor Litviňuková atlas (`data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad`, 486,134 cells) independently replicate in the 54-donor PERIHEART atlas (`data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad`, 392,819 cells; normalized inline and cached at `scratch/phaseE_pseudobulk_cache.pkl`)?

---

## 1. Headline Negative Findings (Reported First)

> [!CAUTION]
> **Summary Finding: Two valid chamber-matched replication tests (`Fibroblast` and `Atrial CM -> Atrial CM`) were executed between the Litviňuková discovery atlas and the PERIHEART replication atlas, and both fail to exceed random chance expectation. A third comparison (`Ventricular CM -> Atrial CM`) is an invalid cross-chamber comparison because PERIHEART contains 100% right atrial appendage tissue (`0` ventricular cells); true ventricular cardiomyocyte replication therefore remains untested.**
>
> 1. **Valid Chamber-Matched Empirical-Null Overlaps Fail (2 of 2 Tested Lineages):**
>    - **Fibroblasts (5,262 shared active genes):** Only **2 genes** (`KLHL5`, `ZNF197`) exceed the per-cohort empirical 95th-percentile threshold with concordant sign (expected under independence = 7.16 genes; **Binomial $p = 0.9937$**; note an earlier prose bullet miswrote `ATPAF1` instead of `ZNF197` from Table 4.1).
>    - **Atrial CM $\rightarrow$ Atrial CM (Chamber-Matched, 6,768 shared active genes):** Only **2 genes** (`GPSM2`, `MIX23`) exceed both empirical 95th thresholds with concordant sign (expected = 5.63 genes; **Binomial $p = 0.9763$**).
>    - **Ventricular CM $\rightarrow$ Atrial CM (Invalid Cross-Chamber Comparison, 6,717 shared genes — Does Not Test vCM Replication):** Comparing Litviňuková ventricular myocytes against PERIHEART right atrial appendage myocytes yields **0 genes** exceeding both empirical 95th thresholds (expected = 6.01 genes; **Binomial $p = 1.0000$**). Because `MYH7`/`IRX4` ventricular myocytes and `MYH6`/`NPPA` atrial appendage myocytes are distinct anatomical and electrophysiological lineages, this comparison cannot evaluate whether ventricular aging biomarkers replicate in ventricular tissue.
> 2. **Discovery Table Genes Do Not Replicate:** Of the 100 cell-type-specific aging genes published in `models/cell_type_genes.json` (which drives the Tournament Discovery surface):
>    - **Fibroblasts (Chamber-Matched):** Exactly **0 / 99** evaluated genes replicate at empirical 95th thresholds. Only **9 / 99** (9.1%) achieve nominal significance ($p < 0.05$) with matching sign in PERIHEART. Only **42 / 99** (42.4%) share the same sign of correlation.
>    - **Atrial Myocytes (Chamber-Matched):** Exactly **0 / 99** replicate at empirical 95th thresholds. Only **13 / 99** (13.1%) achieve nominal significance ($p < 0.05$) with matching sign. Only **45 / 99** (45.5%) share sign.
>    - **Ventricular Myocytes (Untested in Ventricular Tissue; Cross-Chamber vs. PERIHEART Atrial CM):** **0 / 100** cross-chamber overlap at empirical 95th thresholds (10 / 100 nominal $p < 0.05$, 50 / 100 sign match); independent ventricular replication remains **untested** due to the absence of an independent local ventricular `.h5ad` cohort.
> 3. **Genome-Wide Correlation Across Cohorts Is Negative:** The Pearson correlation between gene aging coefficients ($r_{\text{youth}}$) in Litviňuková and PERIHEART is negative across the genome:
>    - **Fibroblasts (Chamber-Matched):** $r = -0.4161$ ($p = 1.96 \times 10^{-219}$, raw sign concordance = 52.28%, **centred sign concordance = 36.89%**).
>    - **Atrial CM $\rightarrow$ Atrial CM (Chamber-Matched):** $r = -0.2296$ ($p = 1.07 \times 10^{-81}$, raw sign concordance = 51.82%, **centred sign concordance = 43.03%**).
>    - **Ventricular CM $\rightarrow$ Atrial CM (Invalid Cross-Chamber):** $r = -0.1868$ ($p = 8.20 \times 10^{-54}$, raw sign concordance = 54.62%, **centred sign concordance = 45.96%**).
> 4. **Mechanistic Origin of the Cross-Cohort Anti-Correlation ($r = -0.4161$):** Gene-property stratification across all 5,262 shared fibroblast genes against Ensembl BioMart GRCh38 annotations (`scratch/grch38_gene_annotations.tsv`) proves that `r_youth` in Litviňuková is heavily driven by **`log10(Genomic Span)` ($r = +0.5509, p < 10^{-300}$) and `log10(Total Intron Length)` ($r = +0.5277, p < 10^{-300}$)** because younger Harvard donors (`H2–H7`, mean `48.2 yr`) were sequenced using **single nuclei** (enriching unspliced intronic pre-mRNA and long genes + `lncRNA` [mean $r_{\text{youth}} = +0.4706$]), whereas older Sanger donors (`D1–D7`, mean `60.0 yr`) were predominantly sequenced using **whole cells** (enriching mature short cytoplasmic mRNAs and mitochondrial transcripts [`10/10` mitochondrial genes have $r_{\text{youth}} < 0$, mean $-0.4531$]). In PERIHEART (`100%` uniform single nuclei across all 54 donors), this suspension confound is absent and reverses direction (`r(r_youth, log10_span) = -0.3495`, mitochondrial mean $r_{\text{youth}} = +0.3683$ [`10/10` $>0$]). Adjusting for genomic span, intron length, biotype, and mean expression reduces the shared anti-correlated variance ($R^2$) by **58.1%** ($r = -0.4161 \rightarrow r_{\text{partial}} = -0.2692$), and within the longest gene quartile (`Q4`), the anti-correlation vanishes completely ($r = -0.0412, p = 0.135$, not significant).

---

## 2. Cohort Characteristics and Empirical Random-Gene Null

### 2.1 Cohort Summary
| Parameter | Litviňuková et al. (Discovery) | PERIHEART Cohort (Replication) |
| :--- | :--- | :--- |
| **Dataset File** | `data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad` (`2.95 GB`) | `data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad` (`2.79 GB`) |
| **Total Cells Analyzed** | 486,134 cells | 392,819 nuclei |
| **Total Donors** | 14 donors (**8 Wellcome Sanger Institute `D1–D7, D11`**, **6 Harvard Medical School `H2–H7`**) | 54 donors (single clinical center, Essen) |
| **Age Range** | 40–75 years (site-confounded: **Sanger `n=8` [`D1–D7, D11`] mean `60.31y` [`52.5–72.5y`, older; `D1–D7` mean `60.0y`, `D11` = `62.5y`]**, **Harvard `n=6` [`H2–H7`] mean `48.2y` [`42.5–57.5y`, younger]**) | 40–90 years (`development_stage` midpoints `45.0–85.0y`, mean `67.41y`, SD `9.80y`) |
| **Chambers Available** | Left/Right Ventricle, Left/Right Atrium, Septum, Apex | **100% Right Atrial Appendage** (`right atrium auricular region`, `392,819 / 392,819` nuclei; **`0` ventricular cells**) |
| **Sequencing Chemistry** | Mixed: `10x 3' v2` (Sanger `D1–D7`), `10x 3' v3` (Harvard `H2–H7` and Sanger `D11` [`48,930` cells: `Sanger-Nuclei`, `Sanger-Cells`, `Sanger-CD45`]) | Uniform: `10x Chromium 3' v3` (`100%` single-nucleus suspension) |
| **Processing Site** | Multi-center (Wellcome Sanger [`n=8`: `D1–D7, D11`, older] + Harvard Medical School [`n=6`: `H2–H7`, nuclei, younger]) | Single center (West German Heart & Vascular Center) |

### 2.2 Empirical Null False-Positive Rate (500 Random Frequency-Matched Genes)
To measure the true background rate of false discoveries induced by donor pseudobulking, 500 random genes with expression frequency matched to active cardiac genes were drawn, and their Pearson correlation with youthfulness ($r_{\text{youth}} = \text{corr}(\text{expr}, -\text{age}) = -\text{corr}(\text{expr}, \text{age})$) was computed.

| Cohort & Cell Type | Donor $n$ | Active Genes | FPR (Nominal $p < 0.05$) | BH-FDR ($q < 0.05$) | Empirical 90th $\|r\|$ | Empirical 95th $\|r\|$ | Empirical 99th $\|r\|$ | Critical Parametric $r_{0.05}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Litviňuková vCM** | 14 | 7,601 | **42.0%** (210/500) | 24.8% (124/500) | 0.7497 | **0.7736** | 0.8358 | 0.5324 |
| **Litviňuková Atrial CM** | 12* | 7,546 | **29.8%** (149/500) | 2.2% (11/500) | 0.6927 | **0.7286** | 0.8233 | 0.5324 |
| **Litviňuková Fibroblast** | 14 | 5,943 | **59.2%** (296/500) | 49.0% (245/500) | 0.7546 | **0.7773** | 0.8223 | 0.5324 |
| **PERIHEART CM (Right Atrial)** | 54 | 8,560 | **22.4%** (112/500) | 0.0% (0/500) | 0.3391 | **0.3855** | 0.4340 | 0.2681 |
| **PERIHEART Fibroblast** | 54 | 6,750 | **17.4%** (87/500) | 0.0% (0/500) | 0.3193 | **0.3559** | 0.3990 | 0.2681 |

*\*Note: 12 donors in Litviňuková have valid atrial CM captures.*

#### Methodological Insights from Empirical Nulls:
1. **The 14-Donor Discovery Set Suffers Catastrophic Site/Chemistry Confounding:** When pseudobulked across only 14 donors, completely random genes have a **42.0% to 59.2% probability** of achieving nominal $p < 0.05$. In fibroblasts, 49.0% even survive standard Benjamini-Hochberg FDR correction. This occurs because the 14 donors are split by center and suspension — **Sanger donors (`D1–D7, D11`, $n=8$, mean `60.31 yr` [`D1–D7` whole cells `10x 3' v2` mean `60.0 yr`; `D11` mixed `Sanger-Nuclei`/`Sanger-Cells`/`Sanger-CD45` `10x 3' v3` age `62.5 yr`]) are older whereas Harvard donors (`H2–H7`, $n=6$, single nuclei, `10x 3' v3`) are younger (mean `48.2 yr`, range `40–60 yr`)**. Consequently, unadjusted age correlation in Cohort 1 primarily captures `Sanger vs Harvard` suspension/center differences alongside donor age.
2. **PERIHEART Provides a Substantially Cleaner Background:** In the 54-donor PERIHEART cohort, the false-positive rate drops to **17.4%** in fibroblasts and **22.4%** in cardiomyocytes, and **0.0% of random genes pass BH-FDR $q < 0.05$**. The critical empirical threshold drops from $|r| > 0.777$ down to $|r| > 0.356$.

---

## 3. Cross-Cohort Replication Intersections, Untested Ventricular Gap & Gene-Property Mechanism

We tested replication across all genes shared and actively expressed in both cohorts ($\ge 5\%$ of cells in both). Concordance requires that the sign of correlation with youthfulness ($r_{\text{youth}} = \text{corr}(\text{expr}, -\text{age})$) matches in both cohorts ($\text{sign}(r_1) = \text{sign}(r_2)$).

### 3.1 Replication Statistics by Cell Type Comparison

| Comparison | Validity | Shared Active Genes | Both Nominal $p < 0.05$ (Same Sign) | Expected Nominal Overlap | Binomial $p$ (Nominal) | Both Empirical 95th (Same Sign) | Expected Emp-95 Overlap | Binomial $p$ (Emp-95) | Genome-Wide $r$ Across Cohorts | Raw Sign Concordance | Centred Sign Concordance (`r - mean(r)`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fibroblast** (Lit14 vs Peri54) | **Valid (Lineage-Matched)** | 5,262 | **132** (2.5%) | 287.4 | $1.0000$ | **2** (0.04%) | 7.16 | **$0.9937$** | $-0.4161$ | 52.28% | **36.89%** |
| **Atrial CM $\rightarrow$ Atrial CM** | **Valid (Chamber-Matched)** | 6,768 | **123** (1.8%) | 195.7 | $1.0000$ | **2** (0.03%) | 5.63 | **$0.9763$** | $-0.2296$ | 51.82% | **43.03%** |
| **Ventricular CM $\rightarrow$ Atrial CM** | **Invalid (Cross-Chamber)** | 6,717 | **224** (3.3%) | 258.2 | $0.9875$ | **0** (0.00%) | 6.01 | **$1.0000$** | $-0.1868$ | 54.62% | **45.96%** |

> [!IMPORTANT]
> **Interpretation of Binomial $p$-Values & Sign-Concordance Centring:**
> 1. Under the null hypothesis of independence between the two cohorts, the observed number of empirical-95th concordant genes in the two valid comparisons (`2` in fibroblasts, `2` in chamber-matched atrial CM) is **less than the number expected by pure chance** (`7.16` and `5.63`; Binomial $p \ge 0.976$).
> 2. Raw sign concordance (`52.28%` in fibroblasts) exceeded 50% despite $r = -0.4161$ solely because both cohorts have a positive global mean $r_{\text{youth}}$ offset (`+0.3337` in Litviňuková, `+0.0833` in PERIHEART). After centring each cohort's $r_{\text{youth}}$ vector (`r - mean(r)`), **centred sign concordance drops to `36.89%`** (fibroblasts) and **`43.03%`** (chamber-matched aCM $\rightarrow$ aCM), matching the theoretical $\frac{1}{2} + \frac{1}{\pi}\arcsin(-0.4161) = 36.34\%$.

### 3.2 Untested Ventricular Cardiomyocyte Replication Scope Limitation
Direct inspection of all `obs` columns in `data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad` (`n_obs = 392,819`) confirms that **100.0% (`392,819 / 392,819`) of PERIHEART nuclei originate from the right atrial appendage** (`tissue = 'right atrium auricular region'`, `UBERON:0006631`; `tissue_free_text = "Tissue samples were taken from the right atrial appendage, from the anatomical site of cardiopulmonary bypass venous cannulation."`), containing `88,561` atrial `cardiac muscle cell` nuclei and **`0` ventricular cardiomyocytes**. A full scan of all 10 `.h5ad` files on the local filesystem confirms that every other cardiac file is either a subsample of the 14 Litviňuková donors (`hca_subsampled_20k.h5ad`, `patient_biopsy_aligned.h5ad`, `reprogramming_timecourse.h5ad`, `models/scvi_model_hca/adata.h5ad`), a merge of Litviňuková + PERIHEART (`cardiac_combined_raw.h5ad`, `cardiac_preprocessed.h5ad`), a carotid/coronary arterial plaque dataset with `0` cardiomyocytes (`patient_plaque_aligned.h5ad`), or a truncated download (`f7c1c579-2dc0-47e2-ba19-8165c5a0e353.h5ad`, `44.0 MB`). Consequently, **independent cross-cohort replication for ventricular cardiomyocytes (`7,601` active vCM genes and the `100` vCM table genes in `models/cell_type_genes.json`) remains untested** and requires acquiring an external multi-donor ventricular snRNA-seq cohort (e.g., Reichart et al. 2022 *Science* or Chaffin et al. 2022 *Nature* non-failing left ventricular controls).

### 3.3 Gene-Property & Partial-Correlation Analysis of the Cross-Cohort Anti-Correlation
To determine why `r_youth` is negatively correlated across cohorts ($r = -0.4161$ in fibroblasts, $r = -0.2296$ in chamber-matched atrial CMs), we annotated all `5,262` shared fibroblast genes and `6,768` shared atrial CM genes with Ensembl GRCh38 gene coordinates, total intron length, exonic feature length, and gene biotype (`scratch/grch38_gene_annotations.tsv`, `scratch/run_part3_analysis.py`):
- **Opposite Gene-Length and Intron-Length Gradients:** In Litviňuková fibroblasts, `r_youth` correlates strongly and **positively** with **`log10(Genomic Span)` ($r = +0.5509, p < 10^{-300}$)** and **`log10(Total Intron Length)` ($r = +0.5277, p < 10^{-300}$)**, whereas in PERIHEART fibroblasts `r_youth` correlates **negatively** with **`log10(Genomic Span)` ($r = -0.3495, p = 5.33 \times 10^{-151}$)** and **`log10(Total Intron Length)` ($r = -0.3354, p = 1.54 \times 10^{-138}$)**.
- **Biotype Inversion (`lncRNA` vs. `mitochondrial`):** Because younger Litviňuková donors (`H2–H7`, Harvard, mean `48.2 yr`) were sequenced from **isolated nuclei** (`Sanger-Nuclei`/`Harvard-Nuclei`) while older donors (`D1–D7`, Sanger, mean `60.0 yr`) included **whole cells** (`Sanger-Cells`), nuclear-retained long non-coding RNAs (`n = 167` `lncRNA`) exhibit mean $r_{\text{youth}} = +0.4706$ (`91.0%` $>0$) in Litviňuková, whereas cytoplasmic mitochondrial genes (`n = 10` `MT-*` genes) exhibit mean **$r_{\text{youth}} = -0.4531$ (`0.0%` $>0$, 10/10 negative)** in Litviňuková vs. **mean $r_{\text{youth}} = +0.3683$ (`100.0%` $>0$, 10/10 positive)** in PERIHEART (`100%` uniform single nuclei).
- **Stratification & Partial Correlation:** Stratifying the 5,262 shared fibroblast genes into quartiles of `log10(Genomic Span)` shows that the cross-cohort anti-correlation is steepest in the shortest genes (**`Q1 Shortest`: $r = -0.4477, p = 7.12 \times 10^{-66}$**) and **disappears completely in the longest gene quartile (`Q4 Longest`: $r = -0.0412, p = 0.135$, NS)** and in `lncRNA` ($r = -0.1137, p = 0.143$, NS). Partial correlation controlling for `log10(Genomic Span)`, `log10(Intron Length)`, `Biotype`, and cohort mean expression attenuates the fibroblast anti-correlation from **$r = -0.4161$ ($R^2 = 17.31\%$) to $r_{\text{partial}} = -0.2692$ ($R^2 = 7.25\%$)**, accounting for **58.1%** of the shared anti-correlated variance.

---

## 4. Candidate Genes Meeting Nominal Thresholds in Both Cohorts (Not Enriched Above Chance)

> [!NOTE]
> **Sign Convention:** In all tables below, $r_{\text{youth}} = \text{corr}(\text{expr}, -\text{age})$. Thus $r_{\text{youth}} > 0$ means **Up in Youth (Down with Age)**, and $r_{\text{youth}} < 0$ means **Down in Youth (Up with Age)**. Earlier drafts labelled $r_{\text{youth}} > 0$ as `"Up with Age"`; the headers and values below are explicitly disambiguated.

### 4.1 Fibroblasts: Top Nominal-Intersection Genes
Genes actively expressed in fibroblasts that pass nominal $p < 0.05$ in both cohorts with matching direction of $r_{\text{youth}}$, sorted by minimum effect size $\min(|r_1|, |r_2|)$:

| Gene Symbol | Ensembl ID | Litviňuková $r_{\text{youth}}$ | Litviňuková $p$ | PERIHEART $r_{\text{youth}}$ | PERIHEART $p$ | Direction ($r_{\text{youth}}$ / Age) | Exceeds Both Emp-95? | Biological Function |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KLHL5** | `ENSG00000109790` | $+0.7978$ | $0.0006$ | $+0.5084$ | $9.0 \times 10^{-5}$ | Up in Youth (Down with Age) | **YES** | Kelch-like protein 5, ubiquitin ligase adaptor |
| **ZNF197** | `ENSG00000186448` | $+0.8262$ | $0.0003$ | $+0.3562$ | $0.0082$ | Up in Youth (Down with Age) | **YES** | Zinc finger transcriptional repressor |
| **C9orf85** | `ENSG00000155621` | $+0.7453$ | $0.0022$ | $+0.4566$ | $0.0005$ | Up in Youth (Down with Age) | NO (PERI only) | Uncharacterized cardiac transcript |
| **UST** | `ENSG00000111962` | $+0.5898$ | $0.0264$ | $+0.4533$ | $0.0006$ | Up in Youth (Down with Age) | NO (PERI only) | Uronyl 2-sulfotransferase, extracellular matrix |
| **COL4A4** | `ENSG00000081052` | $+0.7561$ | $0.0018$ | $+0.4311$ | $0.0011$ | Up in Youth (Down with Age) | NO (PERI only) | Collagen type IV alpha 4 chain, basement membrane |
| **EYA2** | `ENSG00000064655` | $+0.5698$ | $0.0334$ | $+0.4295$ | $0.0012$ | Up in Youth (Down with Age) | NO (PERI only) | EYA transcriptional coactivator and phosphatase 2 |
| **LRFN5** | `ENSG00000165379` | $+0.7062$ | $0.0048$ | $+0.4246$ | $0.0014$ | Up in Youth (Down with Age) | NO (PERI only) | Leucine rich repeat and fibronectin type III domain 5 |
| **ATPAF1** | `ENSG00000123472` | $+0.6084$ | $0.0210$ | $+0.4221$ | $0.0015$ | Up in Youth (Down with Age) | NO (PERI only) | ATP synthase mitochondrial F1 complex assembly factor 1 |
| **PCSK5** | `ENSG00000099139` | $+0.6497$ | $0.0119$ | $+0.4203$ | $0.0016$ | Up in Youth (Down with Age) | NO (PERI only) | Proprotein convertase subtilisin/kexin type 5 |
| **CALCOCO2** | `ENSG00000136436` | $+0.6843$ | $0.0070$ | $+0.4086$ | $0.0022$ | Up in Youth (Down with Age) | NO (PERI only) | Calcium binding and coiled-coil domain 2 (NDP52, mitophagy) |
| **PXDNL** | `ENSG00000147485` | $+0.6272$ | $0.0164$ | $+0.4017$ | $0.0026$ | Up in Youth (Down with Age) | NO (PERI only) | Peroxidasin like |
| **SEMA6A** | `ENSG00000092421` | $+0.7256$ | $0.0033$ | $+0.3930$ | $0.0033$ | Up in Youth (Down with Age) | NO (PERI only) | Semaphorin 6A, cell guidance |
| **NEGR1** | `ENSG00000172260` | $+0.6253$ | $0.0168$ | $+0.3920$ | $0.0034$ | Up in Youth (Down with Age) | NO (PERI only) | Neuronal growth regulator 1 |
| **PLCB1** | `ENSG00000182621` | $+0.6535$ | $0.0113$ | $+0.3868$ | $0.0039$ | Up in Youth (Down with Age) | NO (PERI only) | Phospholipase C beta 1 |
| **GTDC1** | `ENSG00000121964` | $+0.7374$ | $0.0026$ | $+0.3812$ | $0.0045$ | Up in Youth (Down with Age) | NO (PERI only) | Glycosyltransferase like domain containing 1 |
| **PLEKHA7** | `ENSG00000166689` | $-0.5879$ | $0.0270$ | $-0.3790$ | $0.0047$ | Down in Youth (Up with Age) | NO (PERI only) | Pleckstrin homology domain containing A7 |

### 4.2 Cardiomyocytes: Top Nominal-Intersection Genes

#### A. Chamber-Matched Atrial CM $\rightarrow$ Atrial CM
| Gene Symbol | Ensembl ID | Litviňuková $r_{\text{youth}}$ | Litviňuková $p$ | PERIHEART $r_{\text{youth}}$ | PERIHEART $p$ | Direction ($r_{\text{youth}}$ / Age) | Exceeds Both Emp-95? | Biological Function |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GPSM2** | `ENSG00000121957` | $+0.7912$ | $0.0008$ | $+0.4378$ | $0.0009$ | Up in Youth (Down with Age) | **YES** | G-protein signaling modulator 2 |
| **MIX23** | `ENSG00000160124` | $+0.7348$ | $0.0028$ | $+0.4233$ | $0.0014$ | Up in Youth (Down with Age) | **YES** | Mitochondrial import inner membrane translocase subunit |
| **PRCP** | `ENSG00000137509` | $+0.5921$ | $0.0257$ | $+0.5191$ | $0.0001$ | Up in Youth (Down with Age) | NO (PERI only) | Prolylcarboxypeptidase (angiotensin regulation) |
| **VIM** | `ENSG00000026025` | $+0.5627$ | $0.0362$ | $+0.5039$ | $0.0001$ | Up in Youth (Down with Age) | NO (PERI only) | Vimentin (cytoskeletal intermediate filament) |
| **EMC3** | `ENSG00000125037` | $+0.5615$ | $0.0367$ | $+0.4831$ | $0.0002$ | Up in Youth (Down with Age) | NO (PERI only) | ER membrane protein complex subunit 3 |
| **HDX** | `ENSG00000165259` | $+0.6808$ | $0.0074$ | $+0.4670$ | $0.0004$ | Up in Youth (Down with Age) | NO (PERI only) | Highly divergent homeobox |
| **PSMA3** | `ENSG00000100567` | $+0.6896$ | $0.0064$ | $+0.4400$ | $0.0009$ | Up in Youth (Down with Age) | NO (PERI only) | Proteasome 20S subunit alpha 3 |
| **INTS7** | `ENSG00000143493` | $+0.5641$ | $0.0356$ | $+0.4391$ | $0.0009$ | Up in Youth (Down with Age) | NO (PERI only) | Integrator complex subunit 7 |
| **MRPL13** | `ENSG00000172172` | $+0.7030$ | $0.0050$ | $+0.4231$ | $0.0014$ | Up in Youth (Down with Age) | NO (PERI only) | Mitochondrial ribosomal protein L13 |
| **YES1** | `ENSG00000176105` | $+0.7152$ | $0.0040$ | $+0.4207$ | $0.0015$ | Up in Youth (Down with Age) | NO (PERI only) | YES proto-oncogene 1, Src family tyrosine kinase |

#### B. Ventricular CM $\rightarrow$ Atrial CM Cross-Chamber Comparison
| Gene Symbol | Ensembl ID | Litviňuková $r_{\text{youth}}$ | Litviňuková $p$ | PERIHEART $r_{\text{youth}}$ | PERIHEART $p$ | Direction ($r_{\text{youth}}$ / Age) | Exceeds Both Emp-95? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ZHX3** | `ENSG00000174306` | $+0.7615$ | $0.0016$ | $+0.5218$ | $0.00005$ | Up in Youth (Down with Age) | NO (lit $r < 0.7736$) |
| **PRCP** | `ENSG00000137509` | $+0.5937$ | $0.0252$ | $+0.5191$ | $0.00006$ | Up in Youth (Down with Age) | NO |
| **NPR3** | `ENSG00000113389` | $+0.5942$ | $0.0250$ | $+0.4710$ | $0.00033$ | Up in Youth (Down with Age) | NO |
| **TNS2** | `ENSG00000111077` | $+0.5686$ | $0.0339$ | $+0.4674$ | $0.00037$ | Up in Youth (Down with Age) | NO |
| **CALCOCO2** | `ENSG00000136436` | $+0.5670$ | $0.0345$ | $+0.4558$ | $0.00053$ | Up in Youth (Down with Age) | NO |
| **UBAC1** | `ENSG00000130560` | $+0.5693$ | $0.0336$ | $+0.4527$ | $0.00059$ | Up in Youth (Down with Age) | NO |
| **TRIM8** | `ENSG00000171206` | $+0.6817$ | $0.0073$ | $+0.4477$ | $0.00069$ | Up in Youth (Down with Age) | NO |

---

## Part 5 — Genes Exceeding |r| >= 0.30 in Both Cohorts (Not Enriched Above Chance)

Of 5,262 shared genes, 152 (2.89%) exceed $|r| \ge 0.30$ in both cohorts with the same sign, versus 189 (3.59%) with the opposite sign — below the 50% random expectation.

We also evaluated `models/cell_type_genes.json` (the 100-gene lists driving the **Zenith Tournament Discovery surface**) against PERIHEART.

### 5.1 Replicability Summary Across the 100 Table Genes

| Cell Type List | Evaluated Genes in Both | Same Sign in PERIHEART | Replicates Nominal $p < 0.05$ (Same Sign) | Replicates Both Nominal $p < 0.05$ | Replicates PERI Emp-95 (Same Sign) | Replicates Both Emp-95 (Same Sign) | Correlation of $r$ Across 100 Genes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fibroblast** (100 genes) | 99 | **42 / 99** (42.4%) | **9 / 99** (9.1%) | 6 / 99 (6.1%) | 4 / 99 (4.0%) | **0 / 99 (0.0%)** | $r = -0.3403$ ($p = 0.0006$) |
| **vCM** (100 genes) | 100 | **50 / 100** (50.0%) | **10 / 100** (10.0%) | 4 / 100 (4.0%) | 0 / 100 (0.0%) | **0 / 100 (0.0%)** | $r = -0.2126$ ($p = 0.0337$) |
| **Atrial CM** (100 genes) | 99 | **45 / 99** (45.5%) | **13 / 99** (13.1%) | 4 / 99 (4.0%) | 1 / 99 (1.0%) | **0 / 99 (0.0%)** | $r = -0.1910$ ($p = 0.0582$) |

### 5.2 Specific Nominal-Intersection Genes from the Discovery Tables (Not Enriched Above Chance)
Only the following genes from `models/cell_type_genes.json` achieve nominal significance ($p < 0.05$) in PERIHEART with the concordant direction of $r_{\text{youth}}$:

1. **Fibroblast Table (9 / 99 genes):**
   - `NEGR1` (Lit $r_{\text{youth}} = +0.625$, Peri $r_{\text{youth}} = +0.392, p = 0.0034$)
   - `ABCA10` (Lit $r_{\text{youth}} = +0.597$, Peri $r_{\text{youth}} = +0.358, p = 0.0079$)
   - `ENSG00000256947` (Lit $r_{\text{youth}} = +0.559$, Peri $r_{\text{youth}} = +0.358, p = 0.0078$)
   - `DCLK1` (Lit $r_{\text{youth}} = +0.612$, Peri $r_{\text{youth}} = +0.316, p = 0.0197$)
   - `COL4A4` (Lit $r_{\text{youth}} = +0.756$, Peri $r_{\text{youth}} = +0.431, p = 0.0011$)
   - `CALCRL-AS1` (Lit $r_{\text{youth}} = +0.536$, Peri $r_{\text{youth}} = +0.311, p = 0.0219$)
   - `COL4A3` (Lit $r_{\text{youth}} = +0.741$, Peri $r_{\text{youth}} = +0.323, p = 0.0171$)
   - `UST` (Lit $r_{\text{youth}} = +0.590$, Peri $r_{\text{youth}} = +0.453, p = 0.0006$)
   - `ADAMTSL3` (Lit $r_{\text{youth}} = +0.569$, Peri $r_{\text{youth}} = +0.274, p = 0.0448$)

2. **Ventricular CM Table (10 / 100 genes):**
   - `MLIP-AS1` (Lit $r_{\text{youth}} = +0.575$, Peri $r_{\text{youth}} = +0.366, p = 0.0065$)
   - `SH3RF2` (Lit $r_{\text{youth}} = +0.596$, Peri $r_{\text{youth}} = +0.363, p = 0.0070$)
   - `ENSG00000256947` (Lit $r_{\text{youth}} = +0.551$, Peri $r_{\text{youth}} = +0.347, p = 0.0101$)
   - `NFXL1` (Lit $r_{\text{youth}} = +0.654$, Peri $r_{\text{youth}} = +0.334, p = 0.0135$)
   - `KIAA1217` (Lit $r_{\text{youth}} = +0.640$, Peri $r_{\text{youth}} = +0.328, p = 0.0153$)
   - `PLPP3` (Lit $r_{\text{youth}} = +0.559$, Peri $r_{\text{youth}} = +0.320, p = 0.0182$)
   - `MAN1A1` (Lit $r_{\text{youth}} = +0.584$, Peri $r_{\text{youth}} = +0.297, p = 0.0292$)
   - `EDA` (Lit $r_{\text{youth}} = +0.614$, Peri $r_{\text{youth}} = +0.294, p = 0.0308$)
   - `MYH6` (Lit $r_{\text{youth}} = -0.587$, Peri $r_{\text{youth}} = -0.276, p = 0.0433$)
   - `SLC26A3` (Lit $r_{\text{youth}} = +0.605$, Peri $r_{\text{youth}} = +0.275, p = 0.0440$)

3. **Atrial CM Table (13 / 99 genes):**
   - `MLIP-AS1` (Lit $r_{\text{youth}} = +0.603$, Peri $r_{\text{youth}} = +0.366, p = 0.0065$)
   - `KCNJ3` (Lit $r_{\text{youth}} = +0.568$, Peri $r_{\text{youth}} = +0.363, p = 0.0070$)
   - `AGBL4` (Lit $r_{\text{youth}} = +0.547$, Peri $r_{\text{youth}} = +0.363, p = 0.0070$)
   - `SH3RF2` (Lit $r_{\text{youth}} = +0.655$, Peri $r_{\text{youth}} = +0.363, p = 0.0070$)
   - `LRMDA` (Lit $r_{\text{youth}} = +0.638$, Peri $r_{\text{youth}} = +0.354, p = 0.0087$)
   - `LIFR` (Lit $r_{\text{youth}} = +0.563$, Peri $r_{\text{youth}} = +0.352, p = 0.0090$)
   - `AMD1` (Lit $r_{\text{youth}} = +0.561$, Peri $r_{\text{youth}} = +0.351, p = 0.0092$)
   - `EDA` (Lit $r_{\text{youth}} = +0.560$, Peri $r_{\text{youth}} = +0.294, p = 0.0308$)
   - `ENSG00000256947` (Lit $r_{\text{youth}} = +0.545$, Peri $r_{\text{youth}} = +0.347, p = 0.0101$)
   - `NFXL1` (Lit $r_{\text{youth}} = +0.582$, Peri $r_{\text{youth}} = +0.334, p = 0.0135$)
   - `KIAA1217` (Lit $r_{\text{youth}} = +0.598$, Peri $r_{\text{youth}} = +0.328, p = 0.0153$)
   - `RALGPS2` (Lit $r_{\text{youth}} = +0.573$, Peri $r_{\text{youth}} = +0.281, p = 0.0394$)
   - `SLC26A3` (Lit $r_{\text{youth}} = +0.551$, Peri $r_{\text{youth}} = +0.275, p = 0.0440$)

---

## 6. Secondary Pooled OLS Sensitivity Analysis (68 Donors)

To formally test whether adjusting for study and center batch effects rescues the discovery genes, we pooled all 68 donors (14 Litviňuková + 54 PERIHEART) into a single design matrix:
$$\mathbf{y}_g = \beta_{0,g} + \beta_{\text{age},g} \cdot \text{Age} + \beta_{\text{cohort},g} \cdot \mathbf{1}_{\text{PERIHEART}} + \beta_{\text{Sanger},g} \cdot \mathbf{1}_{\text{Sanger}} + \boldsymbol{\epsilon}_g \quad (df = 64)$$

### 6.1 Results of Pooled Multivariable Regression

| Table Gene Panel | Evaluated Donors | Residual Degrees of Freedom | Genes with $p_{\text{age}} < 0.05$ | Genes Retaining Same Direction as Discovery | Percentage Retaining Discovery Signal |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fibroblast Table 100** | 68 donors | 64 | 44 / 100 | **12 / 100** | **12.0%** |
| **vCM Table 100** | 68 donors | 64 | 24 / 100 | **11 / 100** | **11.0%** |
| **Atrial CM Table 100** | 68 donors | 64 | 34 / 100 | **14 / 100** | **14.0%** |

#### Why Did 86%–89% of Discovery Table Genes Fail?
When the `SangerSite` indicator is introduced alongside `Cohort`, the variance previously attributed to "Age" in Litviňuková collapses into the site indicator (`scripts/run_phaseE_cross_cohort_replication.py:480` defines `is_sanger = 1.0 if d.startswith("D") else 0.0`, which already assigns `D11` alongside `D1–D7` to `Sanger`). Because the 8 Wellcome Sanger Institute donors (`D1–D7, D11`, mean age `60.31 yr` [`D1–D7` whole-cell `10x 3' v2` mean `60.0 yr`; `D11` female, `62.5 yr` midpoint, `48,930` cells across `Sanger-Nuclei`, `Sanger-Cells`, `Sanger-CD45` on `10x 3' v3`]) are older than the 6 Harvard Medical School donors (`H2–H7`, mean age `48.2 yr`, single-nuclei `10x 3' v3`), their apparent age associations were primarily technical artifacts of suspension/center differences between the two research centers.

---

## 7. Conclusions & Platform Governance Recommendations

1. **Retire Unreplicated Discovery Targets:** Targets in `models/cell_type_genes.json` that fail both cross-cohort replication and pooled multivariable OLS must be flagged as *unreplicated exploratory hypotheses* rather than verified biomarkers of cardiac aging.
2. **Treat Nominal Overlaps as Candidate Hypotheses Only:** Even genes exceeding nominal thresholds in both cohorts (`KLHL5`, `ZNF197`, `GPSM2`, `MIX23`) do not exceed the random-chance binomial overlap expectation (`2` observed vs `7.16` expected in fibroblasts; `2` observed vs `5.63` expected in atrial CM) and require prospective experimental validation.
3. **Replace the Confounded 14-Donor Clock with Uniform-Chemistry Multi-Donor Calibration:** As documented in Phase D, the 14-donor Litviňuková LODO clock fails ($r = 0.351, p = 0.219$, MAE = 7.31y). By contrast, a ridge-regularized LODO clock (`alpha = 100`, top-100 in-fold features) trained on the uniform-chemistry 54-donor PERIHEART snRNA-seq cohort achieves statistically significant out-of-donor age prediction (**Atrial CM: `LODO MAE = 6.97 yr`, Pearson $r = 0.4606, p = 4.57 \times 10^{-4}$** [`r = 0.4936, p = 1.49 \times 10^{-4}` across all `8,560` active genes]; **Fibroblasts: `LODO MAE = 7.03 yr`, Pearson $r = 0.4467, p = 7.10 \times 10^{-4}$** vs. `8.19 yr` null MAE), despite PERIHEART donor ages being quantized into 10-year `development_stage` bins.

---
*Raw pseudobulk matrices cached at `scratch/phaseE_pseudobulk_cache.pkl` and full tabular results archived in `scratch/phaseE_replication_summary.json`.*
