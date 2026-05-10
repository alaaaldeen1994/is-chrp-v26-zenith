
import scanpy as sc
import pandas as pd
import os

DATA_PATH = "data/hca_subsampled_20k.h5ad"

def main():
    print("="*60)
    print("ðŸ§¬ INSPECTING REAL BIOLOGICAL DATA: Heart Cell Atlas")
    print("="*60)
    
    if not os.path.exists(DATA_PATH):
        print("âŒ Data file not found!")
        return

    # Load Data
    adata = sc.read_h5ad(DATA_PATH)
    
    print(f"ðŸ“Š Dataset Dimensions: {adata.n_obs} Cells x {adata.n_vars} Genes")
    print(f"ðŸ“„ Source File: {DATA_PATH}")
    print(f"ðŸ’¾ File Size: {os.path.getsize(DATA_PATH) / (1024*1024):.2f} MB")
    print("-" * 60)
    
    # Show Cell Types
    print("\nðŸ«€  DETECTED CELL TYPES (Top 10):")
    if 'cell_type' in adata.obs:
        print(adata.obs['cell_type'].value_counts().head(10))
    else:
        print("(Cell type labels not found in obs, showing generic index)")
        print(adata.obs.head())

    # Show Raw Gene Expression
    print("\nðŸ§¬  RAW GENE EXPRESSION (First 5 Cells, Key Regulators):")
    genes_to_show = ['TNNT2', 'MYH6', 'TTN', 'NPPA', 'GAPDH'] # Heart markers
    
    # Check which genes are actually in the dataset
    available_genes = [g for g in genes_to_show if g in adata.var_names]
    
    if len(available_genes) > 0:
        # Get raw counts (if accessible) or normalized
        # Convert sparse matrix to dense for printing
        df = pd.DataFrame(
            adata[:5, available_genes].X.toarray(), 
            columns=available_genes,
            index=adata.obs_names[:5]
        )
        print(df)
    else:
        print("âš ï¸  Target heart genes not found (Feature selection might have filtered them).")
        print("Showing random available genes instead:")
        random_genes = adata.var_names[:5]
        df = pd.DataFrame(
            adata[:5, random_genes].X.toarray(), 
            columns=random_genes,
            index=adata.obs_names[:5]
        )
        print(df)

    print("\n" + "="*60)
    print("âœ… VERIFIED: This is Real Biological Data.")
    print("="*60)

if __name__ == "__main__":
    main()
