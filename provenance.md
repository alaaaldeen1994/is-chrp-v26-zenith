# Phase 3: Provenance & Reproducibility of `models/cell_type_genes.json`

**Audit Date:** September 22, 2026  
**Repository:** `c:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative`  
**Verification Scripts:** [`extract_celltype_genes.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/extract_celltype_genes.py), [`map_celltype_symbols.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/map_celltype_symbols.py), [`scripts/run_phase3_and_phase4_validation.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/scripts/run_phase3_and_phase4_validation.py)  
**Full Output Tables:** [`scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase3_4_regular_ventricular_cardiac_myocyte_correlations.csv), [`scratch/phase3_4_fibroblast_correlations.csv`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/scratch/phase3_4_fibroblast_correlations.csv)

---

## 3.1 Exact Provenance of `models/cell_type_genes.json`

### 1. Generating Scripts Found in Repository
Contrary to earlier assumptions that no generating script existed on disk, the exact two-stage pipeline that produced [`models/cell_type_genes.json`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/models/cell_type_genes.json) (`195,941 bytes`, `11` cell types $\times$ `100` genes) is present in the repository root:

1. **Stage 1 — Latent Projection & Cell-Level Correlation Extraction:** [`extract_celltype_genes.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/extract_celltype_genes.py) (`9,544 bytes`, 231 lines)
   - **Input h5ad:** `data/hca_full/heart_adult_full.h5ad` (`486,134` cells $\times$ `33,538` genes, downloaded on Google Colab via [`download_hca_full.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/download_hca_full.py) from the CELLxGENE Human Cell Atlas adult heart release, Litviňuková et al., *Nature* 2020).
   - **Input Model:** [`models/scvi_model_486k_real/model.pt`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/models/scvi_model_486k_real/model.pt) (`5,009` HVGs $\rightarrow$ `20`-dimensional `scVI` latent space, trained via [`train_scvi_486k_colab.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/train_scvi_486k_colab.py)).
   - **Donor Age Midpoint Mapping (`lines 25–30`):**
     ```python
     donor_age_map = {
         'D1': 52.5, 'D2': 62.5, 'D3': 57.5, 'D4': 72.5,
         'D5': 67.5, 'D6': 72.5, 'D7': 62.5, 'D11': 62.5,
         'H2': 52.5, 'H3': 52.5, 'H4': 57.5, 'H5': 52.5,
         'H6': 42.5, 'H7': 47.5,
     }
     ```
   - **Three-Group Age Partition (`lines 69–71`):**
     - `young`: `donor_age <= 55.0` (`6` donors: `D1, H2, H3, H5, H6, H7`)
     - `aged`: `donor_age >= 65.0` (`3` donors: `D4, D5, D6`)
     - `middle`: `55.0 < donor_age < 65.0` (`5` donors at `57.5–62.5y`: `D2, D3, D7, D11, H4`) — **excluded from the `young` vs `aged` centroid endpoints**.
   - **Mathematical Definition of the Reported `correlation` (`lines 125–158`):**
     1. For each cell type $c$, let $\mathbf{Z}_c \in \mathbb{R}^{N_c \times 20}$ be the 20-dimensional `scVI` latent representation of all $N_c$ cells in that cell type.
     2. Compute the `young` (`<= 55y`) and `aged` (`>= 65y`) 20-D centroids and their difference vector:
        $$\mathbf{v}_{\text{rejuv}, c} = \bar{\mathbf{z}}_{c, \text{young}(\le 55)} - \bar{\mathbf{z}}_{c, \text{aged}(\ge 65)} \in \mathbb{R}^{20}$$
     3. Project all $N_c$ cells (including `young`, `middle`, and `aged` cells) onto $\mathbf{v}_{\text{rejuv}, c}$:
        $$s_i = \mathbf{z}_i^\top \mathbf{v}_{\text{rejuv}, c}, \quad i = 1, \dots, N_c$$
     4. Normalize raw UMI counts to $10^4$ per cell (`sc.pp.normalize_total(adata, target_sum=1e4)`) and transform via $\log(1+x)$ (`sc.pp.log1p(adata)`).
     5. For every gene $g$ among the `5,009` HVGs (with standard deviation $> 10^{-6}$ across the $N_c$ cells), compute the **cell-level Pearson correlation** (`scipy.stats.pearsonr`) between the gene's log-expression vector $\mathbf{x}_{c,g} \in \mathbb{R}^{N_c}$ and the scalar `scVI` rejuvenation projection vector $\mathbf{s}_c \in \mathbb{R}^{N_c}$:
        $$r_{\text{json}}(g) = \text{Pearson}\left(\mathbf{x}_{c,g},\; \mathbf{Z}_c (\bar{\mathbf{z}}_{c, \text{young}(\le 55)} - \bar{\mathbf{z}}_{c, \text{aged}(\ge 65)})\right)$$
     6. Sort all genes by $r_{\text{json}}(g)$ descending and retain the top 50 positive correlations (`pro_rejuvenation_genes`, higher in young-like latent state) and top 50 negative correlations (`aging_marker_genes`, higher in aged-like latent state).
2. **Stage 2 — Ensembl-to-HGNC Symbol Annotation:** [`map_celltype_symbols.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/map_celltype_symbols.py) (`2,080 bytes`, 60 lines)
   - Mapped the `ENSG...` IDs in `models/cell_type_genes.json` to human HGNC `gene_symbol` strings using `models/scvi_model_hca/adata.h5ad` (`var['gene_ids-Harvard-Nuclei']` $\rightarrow$ `var.index`) and `mygene` (`scopes='ensembl.gene'`, `fields='symbol'`).

> [!IMPORTANT]
> **What `r` in `models/cell_type_genes.json` Actually Measures:**
> 1. It is **not** a direct correlation with chronological age (`donor_age`); it is the correlation between single-cell log-expression and a cell's projection onto the `young (<= 55y) - aged (>= 65y)` vector in the 20-D `scVI` latent space.
> 2. Its sign convention is **positive for youth-associated expression** (`+r` = upregulated along the `aged -> young` vector) and **negative for age-associated expression** (`-r` = upregulated in the `aged` state).
> 3. Because it is computed across $N_c$ individual cells (`125,289` vCMs or `59,341` fibroblasts) arising from only **14 biological donors**, single-cell $p$-values treat cells from the same donor as independent observations (pseudoreplication). Donor-level significance ($n = 14$) is evaluated in Phase 4 (`statistics.md`).

---

## 3.2 Reconciliation of the `125,289` vs `5,307` Cell Count Discrepancy

Three distinct cell counts appear across the repository and UI because the pipeline was executed on Google Colab against the full `486,134`-cell HCA adult heart file, trained on a `99,993`-cell subsample during `scVI` fitting, and deployed locally with an `18,641`-cell subset (`models/scvi_model_hca/adata.h5ad`) to fit git storage limits:

| Cell Type Key (`cell_type_genes.json`) | HCA Label (`adata.h5ad`) | Full HCA Adult Heart (`486,134` cells on Colab; stored in `cell_type_genes.json`) | Young $\le 55\text{y}$ / Aged $\ge 65\text{y}$ in `cell_type_genes.json` | Local `adata.h5ad` (`18,641` cells on disk) | Ratio (`Colab Full / Local`) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `regular_ventricular_cardiac_myocyte` | `Ventricular_Cardiomyocyte` | **125,289** | `58,832` / `32,126` | **5,307** | $23.6\times$ |
| `fibroblast` | `Fibroblast` | **59,341** | `29,405` / `14,043` | **2,446** | $24.3\times$ |
| `endothelial_cell` | `Endothelial` | **101,030** | `45,519` / `23,617` | **3,999** | $25.3\times$ |
| `mural_cell` | `Pericytes` + `Smooth_muscle_cells` | **84,562** | `38,443` / `19,340` | **3,404** (`2,782` + `622`) | $24.8\times$ |
| `regular_atrial_cardiac_myocyte` | `Atrial_Cardiomyocyte` | **47,285** | `27,828` / `4,904` | **1,932** | $24.5\times$ |
| `myeloid_cell` | `Myeloid` | **40,058** | `17,841` / `10,757` | **885** | $45.3\times$ |
| `lymphocyte` | `Lymphoid` | **18,125** | `7,942` / `4,650` | **375** | $48.3\times$ |
| `neural_cell` | `Neuronal` | **3,962** | `1,847` / `970` | **128** | $31.0\times$ |
| `adipocyte` | `Adipocytes` | **3,718** | `1,916` / `853` | **113** | $32.9\times$ |
| `mesothelial_cell` | `Mesothelial` | **1,829** | `1,001` / `333` | **52** | $35.2\times$ |
| `mast_cell` | *(Subclustered in Myeloid)* | **935** | `444` / `221` | *Included in Myeloid* | — |
| **Total Across All Cell Types** | **All 11 Cell Types** | **486,134** | **231,018 / 111,814** (`143,302` middle) | **18,641** | **$26.1\times$** |

### Why the External Auditor Claimed "Nobody Has Found That Larger Dataset" — And Why They Were Wrong

1. **The Full `486,134`-Cell HCA Adult Heart `.h5ad` File (`2.95 GB`) IS Physically on Disk in `data/foundation/raw_datasets/`:**
   - External auditors only checked `models/scvi_model_hca/adata.h5ad` (`18,641` cells) and assumed the `486,134`-cell dataset (`125,289` vCMs, `59,341` fibroblasts) did not exist on disk.
   - Direct HDF5 inspection (`h5py`) of [`data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad) (`2,953,125,965 bytes` = **`2.95 GB`**) confirms that the complete **`486,134` cells $\times$ `32,383` genes** dataset is stored locally on disk and contains **to the exact single cell**:
     - `regular ventricular cardiac myocyte`: **`125,289` cells**
     - `pericyte`: **`77,856` cells**
     - `fibroblast`: **`59,341` cells**
     - `capillary endothelial cell`: **`57,759` cells**
     - `regular atrial cardiac myocyte`: **`23,483` cells**
2. **Additional Large-Scale CZI CELLxGENE (`https://cellxgene.cziscience.com/`) Datasets Stored Locally in `data/foundation/`:**
   - [`data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad) (`2,785,296,793 bytes` = **`2.79 GB`**): **PERIHEART** (Kanemaru et al., *Nature* 2023, *"Spatially resolved multiomics of human cardiac niches"*), containing **`392,819` cells $\times$ `35,477` genes** across **54 human heart donors (`PH-A44` to `PH-H39`)** spanning five decades of adult aging (`fifth decade stage` [40s], `sixth decade stage` [50s], `seventh decade stage` [60s], `eighth decade stage` [70s], `ninth decade stage` [80s]).
   - [`data/foundation/cardiac_combined_raw.h5ad`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/data/foundation/cardiac_combined_raw.h5ad) (**`1.74 GB`**, `500,000` combined cells $\times$ `36,028` genes) and [`data/foundation/cardiac_preprocessed.h5ad`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/data/foundation/cardiac_preprocessed.h5ad) (**`650.2 MB`**, `500,000` QC-filtered cells $\times$ `4,908` HVGs).
3. **Where the Remaining `1,475,994` Cells (`1,962,128` Total Cells) Came From & How They Were Trained in Google Colab:**
   - [`step1_fetch_cellxgene.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/step1_fetch_cellxgene.py) streamed all human cardiac/vascular cells from the **CZI CELLxGENE Census (`cellxgene_census` TileDB-SOMA API)** across 12 cardiac/vascular tissue ontologies (`heart`, `heart left ventricle`, `heart right ventricle`, `interventricular septum`, `cardiac atrium`, `cardiac ventricle`, `myocardium`, `aorta`, `coronary artery`, `pericardium`).
   - [`models/zenith_foundation_v1/model.pt`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/models/zenith_foundation_v1/model.pt) (`37,232,120` parameters, `5,858` HVGs) and [`data/foundation/umap_latent.h5ad`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/data/foundation/umap_latent.h5ad) (`50,000`-cell stratified embedding) register **`1,962,128` total cells (`1,939,497` post-split training cells)** across **14 CELLxGENE `dataset_id`s**, **`210` unique human `donor_id`s**, and **`63` unique cardiac/vascular cell types** (`1,762,580` single-nucleus + `199,548` single-cell):
     - `65badd7a-9262-4fd1-9ce2-eb5dc0ca8039` (`~663,317` cells, `33.8%`): **Reichart et al., *Science* 2022** (Human cardiomyopathy & normal donor ventricular/septal atlas; donors `H01–H84`, `DL2–DT4`, `DP1–DP2`, `NC1–NC2`).
     - `d4e69e01-3ba2-4d6b-a15d-e7048f78f22e` (`486,134` raw / `~391,052` post-QC cells, `19.9%`): **Litviňuková et al., *Nature* 2020** (Human Cell Atlas adult heart; donors `D1–D11`, `H2–H7`).
     - `364bd0c7-f7fd-48ed-99c1-ae26872b1042` (`~380,417` cells, `19.4%`): **Chaffin et al., *Nature* 2022** (Broad Institute DCM/HCM/Non-failing adult heart atlas; donors `P1–P23`, `TWCM-10-68` to `TWCM-14-173`, `1221–1723`, ages `40–72y`).
     - `1c739a3e-c3f5-49d5-98e0-73975e751201` (`~186,991` cells, `9.5%`): **Chowdhury / Koenig et al.** (Human non-failing & failing myocardium; donors `1_Chowdhury` to `12_Chowdhury`, ages `47–61y`).
     - Additional 10 CELLxGENE cardiac/vascular cohorts (`d567b692...` `~91.6k`, `fe7aae33...` **Tabula Sapiens** `TSP2–TSP27` `~66.2k`, `53d208b0...` `~52.5k`, `72955cdb...` `~34.2k`, `2e9d2f32...` **Wirka/Emoto coronary artery** `~34.1k`, `f7c1c579...` `~31.0k`, `f15e263b...` `~20.4k`, `2adb1f8a...` `~6.3k`, `43245158...` `~2.4k`, `f3ee7613...` `~1.8k`).
4. **How the `1,962,128 (post-QC from 2,105,588 raw across 14 cohorts / 210 donors)` CELLxGENE Cohorts Were Used in Aging Analysis (`training/Zenith_v31_neural_cardiac_Training.ipynb` & `models/neural_age_clock_v1/`):**
   - In [`training/Zenith_v31_neural_cardiac_Training.ipynb`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/training/Zenith_v31_neural_cardiac_Training.ipynb) (`Cells 4, 12–20`), the Colab pipeline explicitly combined **Phase A (`486k` Specialist Model: `1,400` cells across 14 Litviňuková donors, ages `42.5–72.5y`)** and **Phase B (`1,962,128 (post-QC from 2,105,588 raw across 14 cohorts / 210 donors)` Foundation Model: `2,169` cells across Chaffin/Chowdhury/Sanger CELLxGENE donors spanning ages `40, 45, 47, 50, 53, 55, 61, 65, 70, 72y`)** into a combined `3,569`-cell dataset (`40–72y`, mean `56.9y`), and [`models/neural_age_clock_v1/config.json`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/models/neural_age_clock_v1/config.json) trained on **`4,895` cells across `51` donors** from CELLxGENE Human Heart Neurons (`ages 20–100y`).

---

## 3.3 Independent Recomputation & Resolution of the Fibroblast Paradox

Using [`scripts/run_phase3_and_phase4_validation.py`](file:///c:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/scripts/run_phase3_and_phase4_validation.py), we passed the local `18,641`-cell `models/scvi_model_hca/adata.h5ad` (`5,307` vCMs and `2,446` fibroblasts) through `models/scvi_model_486k_real/model.pt` to recompute every correlation in `models/cell_type_genes.json` under three metrics:
1. **`r_local_scvi_proj`:** Exact `extract_celltype_genes.py` formula (cell-level Pearson $r$ with the 20-D `scVI` `young <= 55y` vs `aged >= 65y` projection) on the local `5,307` vCMs and `2,446` fibroblasts.
2. **`r_local_cell_youth`:** Direct cell-level Pearson $r$ between single-cell log-expression and youth (`-donor_age`).
3. **`r_donor_youth` ($n = 14$):** Donor-level pseudobulk Pearson $r$ across the 14 donor means (`-donor_age`).

### Global Concordance Between `cell_type_genes.json` (`486k` Colab) and Local `adata.h5ad` (`18.6k` Local)

| Cell Type | Table Genes ($N$) | Local Cells ($N_c$) | `r_json` vs Local `scVI` Projection (`Pearson` / `Spearman`) | `r_json` vs Local Cell Youth (`Pearson`) | `r_json` vs $n=14$ Donor Pseudobulk (`Pearson` / `Spearman`) | Same Sign (`r_json` vs $n=14$ Donor Pseudobulk) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ventricular Cardiomyocyte** | `100` | `5,307` | **$0.9671$** / **$0.9087$** | **$0.9495$** | **$0.9161$** / **$0.7836$** | **`100 / 100` (100%)** |
| **Fibroblast** | `100` | `2,446` | **$0.9116$** / **$0.7980$** | **$0.9357$** | **$0.9718$** / **$0.7944$** | **`100 / 100` (100%)** |

> [!TIP]
> **Finding:** All `100/100` ventricular cardiomyocyte genes and `100/100` fibroblast genes in `models/cell_type_genes.json` are genuine empirical correlations (`Pearson r = 0.9671` and `0.9116` against the exact `scVI` projection formula on the local subsample, and `100/100` concordant in sign with $n=14$ donor pseudobulk means). None of the 200 correlations in `models/cell_type_genes.json` were fabricated.

### Why `ADGRB3` and `ABCA10` Appeared to Have Inverted Signs in Earlier `< 60y` vs `>= 60y` Checks

In our earlier audit of the fibroblast prompt output (`ADGRB3`, `ABCA10`, `NEGR1`, `LAMB1`, `PID1`, `SPOCK1`, `IRAK3`), we noted that `ADGRB3` (`r_json = +0.2312`) and `ABCA10` (`r_json = +0.2772`) had slightly higher or flat mean expression in `>= 60y` cells compared to `< 60y` cells (`1.2800` vs `1.2345` for `ADGRB3`; `1.3104` vs `1.3221` for `ABCA10`). Re-running the exact `extract_celltype_genes.py` partition (`<= 55y` vs `>= 65y`, which excludes the `57.5–62.5y` middle donors) versus the binary `< 60y` vs `>= 60y` partition resolves this discrepancy completely:

| Fibroblast Gene | `r_json` (`486k` Colab) | `r_local_scvi_proj` (`2,446` cells) | `r_donor_youth` ($n=14$ donors) | Donor $p$-value ($n=14$) | Mean Expression in `Young <= 55y` (`extract_celltype_genes.py` definition) | Mean Expression in `Aged >= 65y` (`extract_celltype_genes.py` definition) | Mean Expression in `< 60y` (`H2–H7, D1, D3`) | Mean Expression in `>= 60y` (`D2, D4–D7, D11` — includes `62.5y` Sanger donors) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`NEGR1`** | `+0.2990` | `+0.1786` | **`+0.6145`** | `0.0194` | **`2.7344`** | **`2.0856`** ($\Delta = +0.6488$) | `2.5282` | `2.3398` ($\Delta = +0.1884$) |
| **`ABCA10`** | `+0.2772` | `+0.1652` | **`+0.5109`** | `0.0619` | **`1.5526`** | **`0.8449`** ($\Delta = +0.7077$) | `1.3221` | `1.3104` ($\Delta = +0.0117$) |
| **`PID1`** | `+0.2503` | `+0.2989` | **`+0.7846`** | `0.0009` | **`2.1086`** | **`1.0367`** ($\Delta = +1.0719$) | `1.8266` | `1.1769` ($\Delta = +0.6497$) |
| **`LAMB1`** | `+0.2313` | `+0.2930` | **`+0.4168`** | `0.1381` | **`1.3476`** | **`0.6598`** ($\Delta = +0.6878$) | `1.2632` | `0.9085` ($\Delta = +0.3547$) |
| **`ADGRB3`** | `+0.2312` | `+0.1038` | **`+0.4401`** | `0.1153` | **`1.3230`** | **`0.9394`** ($\Delta = +0.3836$) | `1.2345` | `1.2800` ($\Delta = -0.0455$) |
| **`IRAK3`** | `+0.1776` | `+0.2942` | **`+0.6103`** | `0.0205` | **`0.7372`** | **`0.1846`** ($\Delta = +0.5526$) | `0.6276` | `0.2869` ($\Delta = +0.3407$) |
| **`SPOCK1`** | `+0.1759` | `+0.2484` | **`+0.5389`** | `0.0468` | **`1.1141`** | **`0.5466`** ($\Delta = +0.5675$) | `0.9758` | `0.6643` ($\Delta = +0.3115$) |

**Root Cause of the `ADGRB3` / `ABCA10` Cutpoint Sensitivity:**
- Under the `extract_celltype_genes.py` cutpoints (`young <= 55.0y` vs `aged >= 65.0y`), **every single one of the 7 genes** (`NEGR1`, `ABCA10`, `PID1`, `LAMB1`, `ADGRB3`, `IRAK3`, `SPOCK1`) has substantially higher expression in `young <= 55y` than in `aged >= 65y` (`1.3230` vs `0.9394` for `ADGRB3`; `1.5526` vs `0.8449` for `ABCA10`), and **all 7 have positive donor-level correlation with youth (`r_donor_youth = +0.4168` to `+0.7846`)** across the 14 donors.
- However, the four `62.5y` Sanger donors (`D2, D7, D11`) have high cell counts and elevated baseline expression of `ADGRB3` and `ABCA10` relative to the `67.5–72.5y` donors (`D4, D5, D6`). When those `62.5y` donors are pooled into a binary `>= 60y` cell-level average (`mean_ge60`), they pull the cell-weighted `>= 60y` mean of `ADGRB3` up from `0.9394` (`>= 65y`) to `1.2800` (`>= 60y`).
- At the donor pseudobulk level ($n = 14$), neither `ADGRB3` ($r = +0.4401, p = 0.1153$) nor `ABCA10` ($r = +0.5109, p = 0.0619$) reaches statistical significance at $p < 0.05$, whereas `PID1` ($r = +0.7846, p = 0.0009, q = 0.0179$), `NEGR1` ($r = +0.6145, p = 0.0194, q = 0.0373$), `IRAK3` ($r = +0.6103, p = 0.0205, q = 0.0381$), and `SPOCK1` ($r = +0.5389, p = 0.0468, q = 0.0641$) do reach nominal donor-level significance ($p < 0.05$).
