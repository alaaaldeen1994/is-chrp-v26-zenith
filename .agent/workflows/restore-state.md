---
description: restore the project to the January 19th v26.1 Clinical Peak state
---

This workflow restores the "Nilus Lab" project to its most stable, validated clinical state (v26.1 Zenith). Use this if the project data becomes desynced or if the server falls back to "PREVIEW" mode.

### 1. Verification of Local Data
Ensure the following critical files exist in your local directory:
- `models/driftmlp_trained/driftmlp.pt` (AI Brain)
- `models/scvi_model_hca/model.pt` (Clinical Engine)
- `data/real/reprogramming_timecourse.h5ad` (Scientific Validation Data)

### 2. Handling Large Files (Github Bypass)
If the 156MB-190MB files fail to upload:
1. Run `python split_large_file.py` to recreate the 45MB chunks.
2. The `bridge_server.py` is already configured to automatically reassemble these on the server (Railway).

### 3. Deployment Check
// turbo-all
1. Run `git push origin main` to trigger a Railway rebuild.
2. Run `python verify_remote.py` to confirm the site is back in "CLINICAL" mode.

### 4. Critical Settings
- **OPENAI_API_KEY**: Must be set in the Railway "Variables" tab.
- **Lazy Loading**: `bridge_server.py` must stay in `backed='r'` mode to prevent memory crashes on the server.

**Saved Point: Jan 30, 2026 - Ultra-HD 5K Peak (Commit 6f3c96e).**
