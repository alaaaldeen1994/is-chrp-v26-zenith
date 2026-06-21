import numpy as np
import scanpy as sc
import scvi
import json
import torch

def main():
    print("Loading Zenith Foundation v29.0 Model...")
    
    # Load schema
    adata = sc.read_h5ad('models/zenith_foundation_v1/var_schema.h5ad')
    
    # Create dummy data so SCVI can load
    dummy_X = np.zeros((2, adata.n_vars), dtype=np.float32)
    adata = sc.AnnData(X=dummy_X, var=adata.var.copy(), dtype=np.float32)
    adata.layers['counts'] = dummy_X
    
    # Add required covariates
    adata.obs['dataset_id'] = ['1', '1']
    adata.obs['disease'] = ['normal', 'dilated cardiomyopathy']
    adata.obs['cell_type'] = ['cardiac muscle cell', 'cardiac muscle cell']
    adata.obs['donor_id'] = ['D1', 'D1']
    adata.obs['suspension_type'] = ['cell', 'cell']
    
    scvi.model.SCVI.setup_anndata(
        adata,
        layer="counts",
        categorical_covariate_keys=["dataset_id", "disease", "cell_type", "donor_id", "suspension_type"]
    )
    
    # Load Model
    model = scvi.model.SCVI.load('models/zenith_foundation_v1', adata=adata)
    print("Model Loaded. Extracting Decoded Expression...")
    
    # Generate latent representations
    # We will just pass in 0-vectors for latent, but change the disease covariate!
    # Wait, the posterior_predictive_sample allows us to see how the model decodes 'normal' vs 'dilated cardiomyopathy'
    
    latent_z = np.zeros((2, model.summary_stats.n_latent)) # 2 cells, 0 vector
    
    # Run generative model directly (decoder)
    z = torch.tensor(latent_z, dtype=torch.float32).to(model.device)
    
    # Cell 0: normal
    # Cell 1: dilated cardiomyopathy
    # We need the categorical indices.
    cat_covs = []
    for key in model.registry_["setup_args"]["categorical_covariate_keys"]:
        mapping = model.adata_manager.get_state_registry("setup_args").get(key)
        # Actually scvi uses get_from_registry
        pass
        
    # An easier way: model.posterior_predictive_sample automatically uses the obs in adata!
    # Let's decode adata!
    imputed = model.get_normalized_expression(adata, library_size=10000)
    
    # imputed is a DataFrame where rows are cells, cols are genes
    normal_exp = imputed.iloc[0].values
    disease_exp = imputed.iloc[1].values
    
    # We want genes that are HIGH in normal, LOW in disease (Pro-rejuvenation / Normalization)
    # Log2 fold change
    log2fc = np.log2((normal_exp + 1e-6) / (disease_exp + 1e-6))
    
    # Sort genes by Log2FC
    top_indices = np.argsort(log2fc)[::-1]
    
    print("\n--- REAL GENES FROM V29 MODEL ---")
    genes = []
    for i in range(5):
        idx = top_indices[i]
        gene_name = adata.var_names[idx]
        score = log2fc[idx]
        genes.append({"gene": gene_name, "score": float(score)})
        print(f"{i+1}. {gene_name} (Log2FC: {score:.4f})")
        
    with open("scratch/real_v29_genes.json", "w") as f:
        json.dump(genes, f)

if __name__ == "__main__":
    main()
