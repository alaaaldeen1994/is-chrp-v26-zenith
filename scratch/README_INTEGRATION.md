# NEUROS-X Integration for Zenith v31 — Neural Age Clock

> **The first platform to measure both epigenetic age (Horvath) and neural age (functional).**
> Dual-age phenotyping reveals whether aging is genomic or autonomic — a metric no competitor offers.

This module adds a **Neural Age Clock** and **cardiac spiking substrate** to the Zenith platform. It is the first integration point of NEUROS-X into Zenith, enabling a new category of safety and aging assessment.

---

## What's New (Marketing Headline)

| Before (Zenith v30) | After (Zenith v31) |
|---------------------|--------------------|
| Horvath epigenetic age only | **Dual-age**: Horvath (epigenetic) + Neural (functional) |
| Genomic safety only | Genomic + **neural stability** (Φ-hat) |
| "Is the cell younger?" | "Is the cell younger **and** is the heart's nervous system stable?" |
| Single aging phenotype | **Three phenotypes**: concordant, neural-dominant, genomic-dominant |

### The dual-age phenotype (unique IP)

- **Concordant** — epigenetic and neural ages align (uniform aging)
- **Neural-dominant** — neural age > epigenetic (autonomic decline → consider vagal interventions)
- **Genomic-dominant** — epigenetic > neural (genomic drift → consider OSK partial reprogramming)

This classification guides therapeutic choice — no competitor offers this.

---

## File Structure

```
neuros_integration/
├── services/
│   ├── neuros_substrate_service.py   # Spiking cardiac neural substrate (LIF + small-world)
│   └── neural_age_clock.py           # Neural Age Clock + DualAgeComparator
├── routers/
│   └── neural_router.py              # FastAPI endpoints (matches boltz_router.py pattern)
├── database/
│   └── neural_models.py              # SQLAlchemy cache tables (matches models.py pattern)
├── patches/
│   └── horvath_patch.py              # Exact code to add to horvath_clock.py
├── training/
│   └── Zenith_v31_neural_cardiac_Training.ipynb   # Colab notebook to train the clock
└── README_INTEGRATION.md             # This file
```

---

## Installation (5 steps)

### Step 1: Copy files into your Zenith repo

```bash
# From your Zenith repo root:
cp -r neuros_integration/services/neuros_substrate_service.py  services/
cp -r neuros_integration/services/neural_age_clock.py          services/
cp -r neuros_integration/routers/neural_router.py              routers/
cp -r neuros_integration/database/neural_models.py             database/
```

### Step 2: Add the router to bridge_server.py

In `bridge_server.py`, add ONE line (near your existing `app.include_router(boltz_router)`):

```python
from routers.neural_router import router as neural_router
app.include_router(neural_router)
```

### Step 3: Add DualAgeReport to horvath_clock.py

Open `services/horvath_clock.py` and paste the `DualAgeReport` class from `patches/horvath_patch.py` at the bottom of the file. Also add the `/api/v1/horvath/dual-age` endpoint to `bridge_server.py` (shown in the patch file).

### Step 4: Create the database tables

The `NeuralAnalysisCache` and `DualAgeRecord` tables use the same SQLAlchemy Base as your existing `StructureCache`. They will be created automatically on first run. If you use Alembic, generate a migration:

```bash
alembic revision --autogenerate -m "add neural analysis tables"
alembic upgrade head
```

### Step 5: (Optional) Train the clock on your data

Run the Colab notebook `training/Zenith_v31_neural_cardiac_Training.ipynb` to calibrate the neural marker weights on your 486k cell dataset. This produces `models/neural_age_clock_v1/config.json` with learned weights.

If you skip this step, the clock uses literature-based default decline rates (still functional, just not fine-tuned to your data).

---

## API Endpoints

All endpoints follow the same pattern as your Boltz endpoints (async, rate-limited, SHA-256 cached, stripped traces).

### `GET /api/v1/neural/panel`
Returns the neural age marker panel (14 genes across 4 categories).

### `GET /api/v1/neural/substrate`
Returns substrate configuration (512 neurons, 16 clusters, ion-channel genes tracked).

### `POST /api/v1/neural/age`
Predict neural age from gene expression.
```json
// Request
{
  "expression": {"CHAT": 3.2, "TH": 2.1, "NGFR": 1.8, ...},
  "chronological_age": 55,
  "use_cache": true
}
// Response
{
  "neural_age": 61.3,
  "chronological_age": 55,
  "neural_age_gap": 6.3,
  "confidence": 0.82,
  "phi_hat": 0.00452,
  "synchrony": 0.34,
  "interpretation": "Cardiac nervous system appears functionally older...",
  "breakdown": { "n_markers_detected": 12, "category_ages": {...}, ... }
}
```

### `POST /api/v1/neural/analyze`
Run the spiking substrate on an ion-channel profile. Returns Φ-hat, synchrony, ECG proxy.

### `POST /api/v1/neural/compare`
Compare substrate response before/after a perturbation (shows how a gene cocktail changes cardiac electrical activity).

### `POST /api/v1/neural/dual-age` ⭐ THE MARKETING METRIC
Combined Horvath + Neural age assessment.
```json
// Request
{
  "expression": {"CHAT": 3.2, ...},
  "horvath_age": 52.3,    // from your horvath_clock.py
  "chronological_age": 55
}
// Response
{
  "horvath_age": 52.3,
  "neural_age": 61.2,
  "chronological_age": 55,
  "dual_gap": 8.9,        // neural - horvath (positive = neural aging faster)
  "phenotype": "neural_dominant",
  "phenotype_description": "Neural aging outpaces genomic — autonomic decline.",
  "rejuvenation_potential": "moderate",
  "summary": "Dual-age: Horvath 52.3y, Neural 61.2y, Chronological 55. Phenotype: neural_dominant."
}
```

---

## How It Works (Technical)

### The Spiking Substrate (`neuros_substrate_service.py`)

A **Watts-Strogatz small-world graph** of 512 LIF (Leaky Integrate-and-Fire) neurons organized into 16 clusters representing cardiac regions:

| Cluster | Cardiac Region |
|---------|---------------|
| 0 | SA node (pacemaker) |
| 1 | AV node |
| 2-3 | Atria (RA, LA) |
| 4-5 | Ventricles (RV, LV) |
| 6-7 | Conduction (Purkinje, His bundle) |
| 8-9 | Vagal (afferent, efferent) |
| 10 | Sympathetic (stellate) |
| 11-13 | Intrinsic ganglia |
| 14-15 | Coronary plexus, Marshall ligament |

**Ion-channel genes** (16 genes including SCN5A, KCNH2, KCNQ1, HCN4, RYR2, CACNA1C) are encoded as input currents. The substrate fires and produces:

- **Φ-hat** — integration proxy (mutual information between clusters). Higher = more integrated = younger.
- **Synchrony** — population spike synchrony. Extreme values flag arrhythmogenic risk.
- **ECG proxy** — a synthetic trace (operational, not clinical) for before/after comparison.

### The Neural Age Clock (`neural_age_clock.py`)

A weighted linear model over 14 neural marker genes in 4 categories:

| Category | Genes | Role |
|----------|-------|------|
| Parasympathetic | CHAT, SLC18A3, CHRNA7, CHRM2 | Vagal tone (declines with age) |
| Sympathetic | TH, DBH | Sympathetic drive |
| Neuronal health | NGFR, RET, NTRK1, NTN1 | Neuronal survival (declines with age) |
| Identity | PHOX2B, ISL1 | Autonomic neuron identity |
| Conduction | GJA1, GJA5 | Gap junctions (fibrosis replaces with age) |

Each gene has a **literature-based decline rate** (e.g., CHAT declines ~1.8%/year after 40). The clock converts observed expression to an estimated age per gene, then takes a weighted average.

The **substrate enrichment** modulates this linear estimate: high Φ-hat → younger (integrated neural activity), low Φ-hat → older (degraded integration). This is the genuinely novel piece — no other aging clock uses a spiking neural substrate.

### The Dual-Age Comparator

Combines Horvath (epigenetic) + Neural (functional) into a phenotype:

```
dual_gap = neural_age - horvath_age

|dual_gap| < 3  →  concordant       (uniform aging)
dual_gap > 3    →  neural_dominant  (autonomic decline)
dual_gap < -3   →  genomic_dominant (epigenetic drift)
```

This classification guides therapeutic choice and is the headline marketing metric.

---

## Marketing Copy (Ready to Use)

### For your website (profile.html):

> **Zenith v31 — Dual-Age Assessment**
>
> The first platform to measure both **epigenetic age** (Horvath 353-CpG) and **neural age** (functional cardiac nervous system).
>
> Our spiking neural substrate simulates cardiac electrical activity from ion-channel gene expression, computing a Φ-hat integration score that reveals whether your heart's nervous system is aging faster than your genome.
>
> **Three aging phenotypes:**
> - **Concordant** — uniform aging, standard interventions
> - **Neural-dominant** — autonomic decline, consider vagal interventions
> - **Genomic-dominant** — epigenetic drift, consider OSK partial reprogramming

### For investors / pitch deck:

> "Zenith v31 introduces the first dual-age phenotyping system in cardiac regenerative medicine. By combining the Horvath epigenetic clock with a novel neural age clock powered by a spiking cardiac substrate, we can classify patients into three aging phenotypes — each requiring a different therapeutic strategy. This is a category-defining capability that no competitor (Insitro, Recursion, Cellarity) offers."

---

## Honest Limitations

- The neural age clock is **calibrated on literature decline rates** by default. For production accuracy, run the training notebook on your 486k cell dataset.
- The ECG proxy is an **operational visualization**, not a clinical ECG. For clinical claims, validate against real ECG data.
- The Φ-hat modulation is a **research proxy** for neural integration. It is NOT proof of consciousness (per the NEUROS-X claim policy).
- The dual-age phenotype is a **hypothesis-generating classification**, not a clinical diagnosis.

---

## Next Steps (Future Integration Points)

This is the FIRST of four planned NEUROS-X integration points:

1. ✅ **Neural Age Clock** (this module) — fastest marketing win
2. 🔲 **Neural Arrhythmia Blacklist** — add to `clinical_audit_engine.py`
3. 🔲 **ECG simulation during DRP** — add to `dosage_optimization_engine.py`
4. 🔲 **Electrophysiological shift prediction** — add to `perturbation_engine.py`

Each is independent and can be added in any order.

---

## Support

Built by the NEUROS-X team. This module is research-grade and follows the same patterns as your existing Zenith codebase (FastAPI, SQLAlchemy, strip traces, async, SHA-256 caching).

For questions: refer to the inline docstrings in each file.
