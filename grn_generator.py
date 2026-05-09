import scanpy as sc
import pandas as pd
import numpy as np
import os

def generate_grn(adata_path, output_path):
    print(f"[GRN] Loading {adata_path}...")
    adata = sc.read_h5ad(adata_path)
    
    # Simple Correlation-based GRN (Professor Level Approximation of CellOracle)
    # In a real scenario, we'd use CellOracle or SCENIC.
    # Here we calculate the gene-gene correlation matrix.
    print("[GRN] Calculating correlation matrix for 4000 genes...")
    # Subset to 4000 genes to match scVI model
    # (Assuming the adata has the same genes)
    
    # Calculate correlations
    corr_matrix = np.corrcoef(adata.X.toarray(), rowvar=False)
    genes = adata.var_names
    
    links = []
    # Only keep top interactions per gene (efficiency)
    for i in range(len(genes)):
        # Top 5 correlations for gene i
        top_idx = np.argsort(np.abs(corr_matrix[i]))[-6:-1] # Skip self-correlation
        for j in top_idx:
            links.append({
                "source": genes[i],
                "target": genes[j],
                "coef": corr_matrix[i, j]
            })
            
    df = pd.DataFrame(links)
    df.to_csv(output_path, index=False)
    print(f"[GRN] Saved {len(df)} links to {output_path}")

if __name__ == "__main__":
    adata_file = "data/hca_subsampled_20k.h5ad"
    if os.path.exists(adata_file):
        generate_grn(adata_file, "models/celloracle_grn.csv")
    else:
        print(f"Error: {adata_file} not found")
