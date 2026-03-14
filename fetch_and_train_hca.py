
import scvi
import scanpy as sc
import os
import shutil

# Configuration
MODEL_PATH = "models/scvi_model_hca"
EPOCHS = 25 # Fast training for prototype

def main():
    print("="*60)
    print("🌍 CONNECTING TO HUMAN CELL KAGAWEA (HCA) REPOSITORY...")
    print("="*60)

    # 1. Fetch Real Data
    print("⬇️  Downloading Heart Cell KAGAWEA (Subsampled)...")
    try:
        # Try to get the specific Heart Atlas subset
        adata = scvi.data.heart_cell_atlas_subsampled()
        dataset_name = "Heart Cell Atlas"
    except Exception as e:
        print(f"⚠️  Heart KAGAWEA not found: {e}")
        print("🔄 Falling back to PBMC3k (Standard Human Reference)...")
        adata = sc.datasets.pbmc3k()
        dataset_name = "PBMC 3k (Human)"

    print(f"✅ Loaded {dataset_name}: {adata.n_obs} cells x {adata.n_vars} genes")

    # 2. Preprocessing (Standard scRNA-seq pipeline)
    print("🔬 Preprocessing raw counts...")
    sc.pp.filter_genes(adata, min_counts=3)
    adata.layers["counts"] = adata.X.copy() # scVI needs raw counts
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    
    # Select highly variable genes (to capture biological variance)
    sc.pp.highly_variable_genes(adata, n_top_genes=2000, subset=True)
    print(f"🧬 Selected 2,000 Highly Variable Genes for Manifold Learning")

    # 3. Setup scVI
    print("🤖 Initializing scVI Variational Autoencoder...")
    scvi.model.SCVI.setup_anndata(adata, layer="counts")
    model = scvi.model.SCVI(adata, gene_likelihood="nb", n_latent=16) # Match simulation 16D

    # 4. Train
    print(f"🧠 Training model on Real Human Data ({EPOCHS} epochs)...")
    model.train(max_epochs=EPOCHS, accelerator="cpu") # Safe fallback to CPU

    # 5. Save
    if os.path.exists(MODEL_PATH):
        shutil.rmtree(MODEL_PATH)
    
    print(f"💾 Saving trained model to {MODEL_PATH}...")
    model.save(MODEL_PATH, overwrite=True, save_anndata=True)

    print("\n" + "="*60)
    print(f"✅ SUCCESS: Real {dataset_name} Integrated.")
    print("   The bridge_server.py can now serve REAL biological latents.")
    print("="*60)

if __name__ == "__main__":
    main()

