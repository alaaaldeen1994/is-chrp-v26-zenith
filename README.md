# Zenith v31.0: Single-Cell Variational Autoencoder & Transcriptomic Perturbation Platform

Preclinical computational biology platform (Research Use Only) for modeling cellular reprogramming and transcriptomic trajectories using `scvi-tools` conditional variational autoencoders (scVI) across a 5,009-gene cardiac specialist manifold.

## 🚀 Overview
Zenith v31.0 is an in silico hypothesis-generation and transcriptomic analysis workbench. It integrates:
- **scVI Variational Autoencoder Core**: A **3,268,462-parameter** cardiac specialist scVI VAE (`2` hidden layers &times; `128` channels, `20` latent dimensions, `5,009` HVGs) and a **37,234,698-parameter** generalist foundation scVI VAE (`4` hidden layers &times; `1,024` channels, `64` latent dimensions, `5,858` HVGs).
- **Single-Cell Training Atlases**: Cardiac specialist checkpoint trained on **99,993 cardiac cells** stratified from the **486,134-cell** Litviňuková et al. (2020) Human Cell Atlas cohort; generalist checkpoint registered on **1,962,128 single cells**.
- **Multi-Donor Aging Clock Evaluation**: Ridge-regularized pseudobulk aging clock achieving **LODO Pearson $r = 0.4606$ ($p = 4.57 \times 10^{-4}$, MAE = $6.97\text{ yr}$)** across 54 uniform-chemistry PERIHEART human right atrial donors (`392,819` nuclei).
- **In Silico Screening & Safety Gate**: Latent perturbation screening coupled with a 12-channel cardiomyocyte leaky integrate-and-fire electrophysiological simulation (`0 / 516` candidate cocktails passing the dual rejuvenation + safety gate; `NL-101` eliminated).

## 🛠️ Technology Stack
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Tailwind + Custom Effects), Three.js, Chart.js.
- **Backend**: FastAPI (Python), PyTorch, `scvi-tools` (Single-Cell Variational Inference).

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
See the [technical_catalog.html](technical_catalog.html) for exhaustive biological logic and protocol specifications.

---
**Developed by Nilus Lab | Institute of Computation**
