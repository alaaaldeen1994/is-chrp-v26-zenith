import scvi
import anndata
import os

def probe_hca():
    print("Fetching Heart Cell Atlas (subsampled)...")
    try:
        adata = scvi.data.heart_cell_atlas_subsampled()
        print(f"Dataset Dimensions: {adata.shape}")
        print(f"Top 10 Genes: {adata.var_names[:10].tolist()}")
        print(f"Cell Types: {adata.obs['cell_type'].unique().tolist()[:5]}...")
        
        # Check if genes are symbols or ENSG
        is_ensg = any(name.startswith('ENSG') for name in adata.var_names[:10])
        print(f"Nomenclature: {'Ensembl (ENSG)' if is_ensg else 'Gene Symbols'}")
        
    except Exception as e:
        print(f"ERROR: Could not fetch HCA data: {e}")

if __name__ == "__main__":
    probe_hca()
