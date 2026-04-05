# Technical Catalog Implementation Gap Report

After a massive audit reviewing the `technical_catalog.html` specifications versus our actual repository logic (`index.html`, `script.js`, `bridge_server.py`), I have identified several key features that are described as functioning in the catalog but are currently **missing** from our codebase.

### 1. "DOWNLOAD DATA" Simulation Export (Section 21)
- **Catalog Claim:** The UI should have a `DOWNLOAD DATA` button that exports the entire simulation state, telemetry metrics, and individual cell traits into a structured JSON file so users can analyze the trajectory offline.
- **Codebase Reality:** There is no `DOWNLOAD DATA` functionality or button implemented in `index.html`, and `script.js` lacks the JSON compilation logic required for this.
- **Action Required:** We need to add a "Download Data" export button to the `index.html` navigation or telemetry panel and write the JS logic to serialize `cells[]` and download it as `simulation_export.json`.

### 2. HD Genome Explorer 5000-Gene Matrix (Section 11)
- **Catalog Claim:** The right-side "Analytics Panel" features an interactive `HD Genome Explorer`—a 5-column scrollable grid where users can search and view all 5,000 explicit gene targets color-coded by expression levels (blue=low, yellow=high).
- **Codebase Reality:** The UI in `index.html` only lists basic HUD metrics and logs. There is no interactive 5,000-gene search box or scrolling data grid constructed in the analytics sidebar.
- **Action Required:** Design and integrate the `HD Genome Explorer` UI in `index.html` and wire it in `script.js` to render the 5,000-point weight array from the backend.

### 3. Enterprise Virtual Trials "Cohort-X" Backend Subsystem (Section 26)
- **Catalog Claim:** The Enterprise Portal handles Phase III virtual trials with an endpoint mapping: `POST /api/v1/clinical/cohort-simulation` which creates thousands of digital twins via PyTorch.
- **Codebase Reality:** While the user-facing `trials.html` exists visually, the `bridge_server.py` FastAPI backend **does not** contain the `/api/v1/clinical/cohort-simulation` route or the underlying tensor noise logic needed to scale up and run these high-throughput cohort calculations.
- **Action Required:** Implement the `cohort-simulation` endpoint in `bridge_server.py` and ensure `trials.html` actually pings it for execution rather than mocking.

### 4. Direct Opentrons Python Protocol Bridge (Section 28)
- **Catalog Claim:** Zenith acts as an "Autonomous Cellular Foundry" where DRP resonance sequences are output directly as robotic fluid-handling logic using the `opentrons.protocol_api`. 
- **Codebase Reality:** The catalog displays a hardcoded script block, but there's no actual dynamic bridge, generation export, or dedicated script (e.g., `generate_opentrons_protocol.py`) embedded in the core app.
- **Action Required:** Create a generation endpoint or function that translates the discovered target manifest directly into a ready-to-run `.py` Opentrons file containing the exact volumetric specifications in the format shown.

### 5. Multi-Mode Microscopy Styles (Section 15)
- **Catalog Claim:** A "CYCLE: FLUORO / PHASE / IMMUNO" button enables users to switch the 2D render state from fluorescence glow, to Phase Contrast translucent halos, to Immuno multi-channel stains.
- **Codebase Reality:** The 2D viewport draws standard stylized circles, but the advanced multi-channel shader cycling UI button doesn't exist on `index.html` or in `script.js`.
- **Action Required:** Enhance the Javascript Canvas drawing loop with specific rendering flags and introduce the mode toggle switch in the UI.

---
**Summary:** Currently, the system has excellent AlphaFold generation and back-end connectivity, but the heavy analytical tools (Downloading JSONs of state, exploring the 5k genes in depth) and Opentrons robot outputs highlighted in the documentation need to be physically added to the code.
