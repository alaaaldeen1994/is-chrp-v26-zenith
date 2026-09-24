<USER_REQUEST>
# Zenith — Final Remediation Plan (verify first, then fix)

## How to use this document

**Nothing is changed until Phase A is complete and the founder has reviewed it.**

Every task begins with **CHECK FIRST**. Much of this may already be done — applied in an earlier
session, fixed weeks ago, or sitting in a folder nobody has opened. **If something already exists
and is correct, do not touch it.** Report it as already done, name the file or line, and move on.

A previous inventory produced at least one confirmed false negative (it reported the 486,134-cell
`.h5ad` as NOT FOUND because it searched `data/hca_full/` instead of
`data/foundation/raw_datasets/`). So searches in this plan must be **filesystem-wide by filename
pattern and content**, never by expected path.

Order: Phase A → **GATE** → B → C → D → E → F → G.

## Prime directives

1. No hardcoded scientific results. No literal assigned to any metric, score, or rank.
2. No code may branch on a gene's or candidate's identity.
3. "Already done", "already correct", "cannot compute" and "this is not real" are all correct,
   complete answers.
4. Never tune anything to produce a desired outcome.
5. Report negative findings first, in plain language.
6. Cite `file:line` for code; path, size, modified date for files.
7. Do not delete or rewrite working code, models, datasets, CSS or UI layout. Changes are
   surgical and named.
8. Strip local paths, usernames and machine identifiers from all outputs.

---

# PHASE A — VERIFICATION GATE (check everything, change nothing)

## A.1 The NL-101 definition — highest priority

Two different factor sets are in circulation across your own documents:

- `SIRT1 + SIRT6 + GATA4 + ZBTB16` (pitch deck, earlier audit documents)
- `SIRT6 + ZBTB16 + GATA4 + NKX2-5` (master report, lines 72 and 77)

**These are different cocktails.** SIRT1 is a deacetylase; NKX2-5 is a cardiac master
transcription factor.

Grep every occurrence of `NL-101`, `NL101`, `nl101` across the entire repository — Python, HTML,
JS, JSON, CSV, Markdown, notebooks. For each hit report `file:line`, the factor set defined there,
and which code path uses it.

Then answer explicitly:

1. Does the codebase contain one definition or more than one?
2. Which factor set did `run_zenith_screening_pipeline.py` actually screen?
3. Which factor set produced the `-0.0085y` figure in `screen_output.csv`?
4. Which factor set is in the pitch deck and on the website?
5. If they differ, **which ablation and screen results refer to which molecule?**

**Do not pick one and standardise yet. Report and stop.** This is the company's lead asset and
the founder decides.

## A.2 Which fixes are already applied?

For each, report ALREADY DONE (with `file:line`) or NOT DONE:

| # | Item |
|---|---|
| 1 | `r = 0.999` rule removed from **both** locations (`~6754–6758` and `~7423`) |
| 2 | `_validate_panel_against_table` guard present and active on all response paths |
| 3 | OT-2 export disabled (UI button and backend route) |
| 4 | Wet-Lab Dossier disabled (UI button and backend route) |
| 5 | `VERIFIED SAFE` / `approved for wet-lab validation` strings removed |
| 6 | `neuros_substrate_service.py` no longer returns `VERIFIED_SAFE` |
| 7 | Harvard / Adiv A. Johnson attribution removed from `index.html` |
| 8 | LNP panel relabelled as illustrative |
| 9 | scGPT label removed or corrected |
| 10 | `CLINICAL+` removed from `technical_catalog.html` |
| 11 | `Phase 4 validated` removed / renamed |
| 12 | `GOLD VALIDATED` / `v33.4_GOLD [PASS]` badges removed |
| 13 | `~500M` / `3.03B` parameter claims corrected |
| 14 | `16 attention heads` / `Transformer` descriptions corrected |
| 15 | `2.42M cells` claim corrected |
| 16 | The Ensembl→symbol mapping bug in `gene_to_idx` (see C.1) |

## A.3 Filesystem-wide re-sweep

Search the **whole filesystem**, by pattern and by content, not by expected path:

1. **Wet-lab data of any kind** — `*.fastq*`, `*.bam`, `*.fcs`, plate-reader CSV, microscopy
   (`*.tif`, `*.czi`, `*.nd2`), qPCR exports, culture logs. Previously reported NOT FOUND; verify.
2. **Benchmark or holdout evaluation outputs** — any script or log computing `99.8%`, `98.2%`,
   `280%`, or `0.982`. Previously NOT FOUND; verify.
3. **Any other `.h5ad`, `.loom`, `.rds`, `.zarr`** above 100 MB anywhere on disk, with `n_obs`,
   `n_vars`, donor count and study of origin.
4. **Opentrons connection logs or telemetry.** Previously NOT FOUND; verify.
5. **Any existing PERIHEART analysis** — scripts, notebooks or outputs referencing
   `f1606894`, `PERIHEART`, `Kanemaru`, or `development_stage`.
6. **Any existing cross-cohort or replication analysis.**

## A.4 The five open inconsistencies

Report the true value and every location where a conflicting value appears:

| Item | Values in circulation |
|---|---|
| `zenith_foundation_v1` `n_latent` | 64 (inventory) vs 128 (master report) |
| Specialist parameter count | 2,649,170 vs 2,649,330 |
| Foundation parameter count | 37,234,698 vs 37,232,120 |
| LODO clock MAE | 6.85y vs 7.31y — and which analysis produced each |
| Synergy bonus description | `+1.65` additive vs `1.35×` multiplicative |

For the clock, also report the **r and p-value** alongside each MAE figure.

## A.5 PERIHEART characterisation (read-only)

From `data/foundation/raw_datasets/f1606894-...h5ad`, report:

1. `n_obs`, `n_vars`, and the full `obs` column list
2. All 54 donor IDs with `development_stage`
3. Cell-type counts, specifically ventricular cardiomyocytes and fibroblasts
4. **The confound structure** — cross-tabulate `development_stage` against every available
   technical variable: `assay`, `suspension_type`, `tissue`, `donor_id`, sex, sequencing depth,
   percent mitochondrial, any site or batch field
5. Whether gene identifiers are Ensembl or symbol, and the overlap with the Litviňuková gene space

**This determines whether PERIHEART can serve as a replication cohort at all.** If age is
confounded with assay inside PERIHEART too, say so — that is a finding, not a failure.

## 🚦 GATE — Deliver `verification.md` and STOP

Open with the answer to A.1 in one paragraph. Then A.2–A.5. **Wait for the founder.**

---

# PHASE B — Resolve the NL-101 definition

Only after the founder decides which factor set is the asset.

Then: make every document, code path, deck and page use that one definition, and state clearly in
the record which prior results refer to which molecule. Any result computed on the other factor
set must be relabelled, not silently reassigned.

---

# PHASE C — Fix the ion channel mapping bug

## C.1 The bug

`train_real_486k_scvi_rebuild_colab.py` deliberately forced 9 cardiac ion channel genes into the
5,009-gene HVG set so the model would contain them. But `neuros_substrate_service.py` looks them
up by symbol against an Ensembl-keyed `gene_to_idx`, the lookup fails, `ion_expr` defaults to
`0.0`, and the panel returns its baseline state **for every input**.

**CHECK FIRST:** is this already fixed? If not:

1. Report which identifier space `gene_to_idx` uses and which the lookup passes
2. Fix the mapping so the 11 protected genes resolve
3. Re-run the panel on three different cocktails and show that outputs now **differ**
4. Report what the panel produces now versus the old constant

## C.2 What this does and does not fix

Fixing the lookup makes the LIF network respond to input. It does **not** make it an arrhythmia
assay — it still has no action-potential morphology and no spatial domain. The relabelled,
limitation-stated framing from Phase 2 stays exactly as it is.

## C.3 Add it to the record

The finding that every `VERIFIED SAFE` ever displayed was a mapping failure returning a default
must appear in the negative-findings section of the master report. It is currently only in
`code_ui_fixes.md`.

---

# PHASE D — Correct how the statistics are reported

The numbers are right. The framing inverts their meaning.

## D.1 Lead with the empirical null

The donor-level analysis found **143/500 random genes reach p < 0.05** — a 28.6% false-positive
rate where 5% is expected, caused by the age/centre collinearity.

When the null is inflated to 28.6%, "48/100 survive BH q < 0.05" is not interpretable as 48 real
signals. BH controls FDR under a valid null; this null is not valid.

**Rewrite section 4.1 to lead with the empirical-null counts:**

- vCM: **7/100** exceed the 95th percentile of the matched random distribution (|r| > 0.7230)
- Fibroblast: **18/100**

Keep the nominal and BH figures, but clearly subordinate and with the inflation stated next to
them.

## D.2 Make the clock's failure a headline finding

The LODO clock reports **r = 0.351, p = 0.219**. It does not significantly predict age across its
own donors. That currently sits in a parenthetical inside a table about website claims.

Promote it to a named negative finding, and state the consequence: **no age-delta figure from this
clock can be reported in either direction**, including the +0.1214y and −0.0085y screen outputs,
which should be described as "not distinguishable from zero by a clock that is itself not
predictive."

## D.3 State the confound's scope precisely

The batch confound applies to `cell_type_genes.json`, computed only on the 14 Litviňuková donors —
which is what the live Tournament Discovery endpoint serves. The 210-donor foundation model is
batch-corrected but is **not** used to generate those tables.

The record should not imply that having a larger model elsewhere mitigates a confound in the table
the product actually reads. Add a short section stating which asset serves which surface.

---

# PHASE E — Cross-cohort replication (the main scientific work)

## E.1 Replicate, do not pool

**Read this before writing any code.** An earlier proposal was to recompute `cell_type_genes.json`
across all 68 donors (14 Litviňuková + 54 PERIHEART) so the table would be "completely free of the
Sanger/Harvard batch confound." **That is not what pooling does.**

Pooling two cohorts replaces a within-study confound with a **study-level batch** — and because
the two cohorts have different age distributions, that new batch variable is itself correlated with
age. Pooling cannot remove confounding; it relocates it.

**The correct design is independent replication:**

1. Compute the aging analysis **separately** in each cohort, at donor level
2. **Intersect** the results
3. A gene that tracks age in both cohorts independently — different donors, different processing,
   different study — is not a batch artifact

This is the strongest evidence available from data already on disk, and it is what a reviewer will
ask for.

## E.2 Per-cohort donor-level analysis

Run identically and independently in each cohort:

**Cohort 1 — Litviňuková** (14 donors, from the 486,134-cell file, not the 18,641 subset)
**Cohort 2 — PERIHEART** (54 donors)

For each cohort, for each gene, for ventricular cardiomyocytes and fibroblasts separately:

1. Per-donor pseudobulk mean (state normalisation)
2. Pearson and Spearman r against donor age, continuous
3. 95% CI, p, BH q
4. **The matched-random empirical null** — 500 detection-frequency-matched genes, same test, report
   the false-positive rate and the 95th-percentile |r| **for that cohort**

Report the empirical null per cohort. PERIHEART's may be far better than Litviňuková's 28.6%; if
so, that is a significant and reportable result on its own.

## E.3 Replication intersection

1. Genes reaching the cohort-specific empirical-null threshold in **both** cohorts
2. Sign concordance across cohorts for those genes
3. Correlation between cohort-1 r and cohort-2 r across all shared genes
4. How many of the current 100 vCM and 100 fibroblast table genes replicate
5. **The binomial probability** of the observed overlap under independence — is the overlap itself
   better than chance?

## E.4 Batch-aware sensitivity, reported alongside

As a secondary analysis only, pool the cohorts **with cohort as an explicit covariate** and report
age effects adjusted for it. Report it beside the replication result, never instead of it, and
state plainly that pooling introduces a study-level batch rather than removing confounding.

## E.5 If PERIHEART is also confounded

If A.5 shows age confounded with assay or suspension type inside PERIHEART, **do not proceed as
if it were clean.** Report the confound, run the analysis within the largest unconfounded stratum
if one exists, and state the limitation. A negative result here is a real finding and cheaper to
learn now.

## E.6 Deliverable

`replication.md` — per-cohort tables, per-cohort nulls, the intersection, the binomial test, and a
plain statement of how many genes survive independent replication. Negative results first.

---

# PHASE F — Reconcile the inconsistencies

Using A.4: pick the verified value for each, correct every location, and record the correction.
Report `file:line` for each change.

Small individually. But a reviewer who finds one inconsistency starts checking all of them, and
that reflex is what you are trying not to trigger.

---

# PHASE G — Honest capability statement

`capability_statement.md`, written for an investor's technical advisor.

1. **Claim ledger** across website, UI and deck: every quantitative claim marked **SUPPORTED** /
   **RESTATE** (with the corrected value) / **REMOVE**.
2. **What the platform does today** — what is computed, what is looked up, what is illustrative,
   what is absent. Plain language, no hedging in either direction.
3. **The replication result from Phase E**, stated as whatever it is.
4. **What would make each removed claim real** — data, method, compute, expertise, time. Unpadded.
5. **Corrected copy** for `index.html`, `how_it_works.html`, `technical_catalog.html`.

---

# Deliverables

| Phase | File | Gate |
|---|---|---|
| A | `verification.md` | **STOP — founder decides on NL-101** |
| B | `nl101_resolution.md` | Report before C |
| C | `ion_channel_fix.md` | Report before D |
| D | Corrected `statistics.md` + master report | Report before E |
| E | `replication.md` | Report before F |
| F | `reconciliation.md` | Report before G |
| G | `capability_statement.md` | Final |

Plus `scripts/` — seeded, runnable, one per analysis.

---

# Definition of success

An accurate picture, not a favourable one.

Each of these would be a **successful** outcome:

- Few or no genes replicate across the two cohorts
- PERIHEART is also confounded
- The NL-101 definition turns out to be inconsistent in the codebase
- The clock cannot support any age claim
- Most website benchmarks have no computation behind them

Each is better established now than discovered later by someone else.

**Where something is already done and correct, leave it alone and say so.** The goal is a platform
whose every claim survives a reviewer opening the code — not a larger diff.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-22T17:21:52+01:00.
</ADDITIONAL_METADATA>