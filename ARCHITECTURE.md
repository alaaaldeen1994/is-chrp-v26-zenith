# Nilus Lab Zenith v31

Repo: C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\

## Frontend
- index.html (Dashboard)
- structure.html (3D Folding)
- profile.html (User dashboard)
- about.html, evidence.html, trials.html, whitepaper.html, legal.html, regulatory.html, contact.html

## Backend
- bridge_server.py (main server, port 9999)

## Core Engines
- perturbation_engine.py (scVI)
- clinical_audit_engine.py (safety)
- dosage_optimization_engine.py (DRP)
- horvath_clock.py (epigenetic age)

## Services (/services)
- boltz_service.py
- structural_folder.py
- horvath_clock.py
- neuros_substrate_service.py (NEW)
- neural_age_clock.py (NEW)

## Routers (/routers)
- api_v1.py
- boltz_router.py
- neural_router.py (NEW)

## Database (/database)
- models.py
- neural_models.py (NEW)

## Models (/models)
- zenith_foundation_v1 (1.94M cells)
- scvi_model_486k_real (486k cells)

## NEW NEUROS-X Endpoints
- GET /api/v1/neural/health
- POST /api/v1/neural/age
- POST /api/v1/neural/dual-age (marketing metric)

## Stats
- 2.426M scVI cells
- 512 LIF neurons
- 14 neural markers
- 2 aging clocks (Horvath + Neural)
- 3 phenotypes (concordant, neural-dominant, genomic-dominant)
