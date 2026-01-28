import scvi
import numpy as np
import pandas as pd
import anndata as ad
import os
import torch

# Configuration
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "scvi_model")
os.makedirs(os.path.dirname(MODEL_DIR), exist_ok=True)

# 1. Define Gene Symbols (must match bridge_server.py)
GENE_SYMBOLS = [
    "POU5F1", "NEUROD1", "NKX2-5", "MYC", "SOX2", "KLF4", 
    "NANOG", "TP53", "GATA4", "PAX6", "TBX5", "CHRNA1"
]

# We also need more genes to fill up to 20,000 for a "real" feel
# In a real model, this would be the full transcriptome
EXTRA_GENES = [f"GENE_{i}" for i in range(20000 - len(GENE_SYMBOLS))]
ALL_GENES = GENE_SYMBOLS + EXTRA_GENES

def generate_mock_model():
    print("Generating synthetic data (150 cells x 20,000 genes)...")
    
    # 2. Create synthetic expression data
    data = np.random.poisson(lam=1.0, size=(150, len(ALL_GENES)))
    
    # 3. Create AnnData object
    adata = ad.AnnData(data.astype(np.float32))
    adata.var_names = ALL_GENES
    adata.obs_names = [f"CELL_{i}" for i in range(150)]
    
    # Setup scVI
    scvi.model.SCVI.setup_anndata(adata)
    
    print("Initializing scVI model architecture...")
    model = scvi.model.SCVI(adata, n_latent=10, n_layers=1)
    
    print("Training model for 2 epochs...")
    model.train(max_epochs=2, batch_size=32)
    
    print(f"Saving model to {MODEL_DIR}...")
    # Clean the directory first
    if os.path.exists(MODEL_DIR):
        import shutil
        try:
            shutil.rmtree(MODEL_DIR, ignore_errors=True)
        except:
            pass
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Save WITH anndata to ensure attr.pkl is created
    model.save(MODEL_DIR, overwrite=True, save_anndata=True)
    
    # Verify files
    files = os.listdir(MODEL_DIR)
    print(f"Files saved in {MODEL_DIR}: {files}")
    
    try:
        print(f"Verifying load from {MODEL_DIR}...")
        test_model = scvi.model.SCVI.load(MODEL_DIR, adata=adata)
        print("VERIFICATION SUCCESS: Model loaded back successfully.")
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")

    if "model.pt" in files:
        print("\nSUCCESS: scVI model weights generated.")
    else:
        print("\nERROR: model.pt not found.")

if __name__ == "__main__":
    generate_mock_model()
