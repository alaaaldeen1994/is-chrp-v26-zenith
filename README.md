# IS-CHRP v26.1 Zenith: Generative Neural SDE Simulation

Professional-grade biological simulation engine for cellular reprogramming and rejuvenation, utilizing Deep-Parameter Neural SDEs (Zenith V28) and real-time transcriptomic manifold visualization.

## 🚀 Overview
IS-CHRP (In-Silico Cellular Health & Reprogramming Protocol) v26.1 Zenith is a high-fidelity diagnostic and simulation tool designed for clinical digital twins. It integrates:
- **Neural SDE Core**: 9.4M parameter "Zenith" model for 1,000-gene regulatory dynamics.
- **Biological Engine**: Real-time 3D latent space projection (UMAP/t-SNE) with HCA (Human Cell Atlas) baseline alignment.
- **High-Fidelity Microscopy**: GPU-accelerated canvas rendering of colony dynamics with sub-cellular detail.
- **Autonomous Discovery**: Differentiable perturbation engine (Biological Gradient Descent) for optimal protocol design.

## 🛠️ Technology Stack
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Tailwind + Custom Effects), Three.js, Chart.js.
- **Backend**: FastAPI (Python), PyTorch (Neural SDE), scvi-tools (HCA Integration).

## 🏃 Getting Started

### 1. Prerequisites
- Python 3.9+
- OpenAI API Key (For AI Assistant features)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Launching the System
1. **Start the Brain (Backend)**:
   ```bash
   python bridge_server.py
   ```
2. **Open the Interface**:
   Double-click `index.html` or open it in a modern web browser (Chrome/Edge recommended).

## 📄 Documentation
See the [v26_technical_catalog.html](v26_technical_catalog.html) for exhaustive biological logic and protocol specifications.

---
**Developed by Nilus Lab | Institute of Computation**
