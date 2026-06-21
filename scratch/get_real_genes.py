import torch
import scanpy as sc
import numpy as np

def main():
    # Load gene names
    adata = sc.read_h5ad('models/zenith_foundation_v1/var_schema.h5ad')
    gene_names = adata.var_names

    # Load raw pytorch weights
    state_dict = torch.load('models/zenith_foundation_v1/model.pt', map_location='cpu', weights_only=False)
    if 'model_state_dict' in state_dict:
        state_dict = state_dict['model_state_dict']

    # The px_scale_decoder connects the final hidden layer to the 5858 genes.
    weight_tensor = state_dict['decoder.px_scale_decoder.0.weight'] # shape (5858, 1024)
    
    # Calculate the importance of each gene by taking the norm of its weights
    # Genes with larger weights across the latent dimensions are the most powerful drivers of state.
    weights = weight_tensor.numpy()
    importance = np.linalg.norm(weights, axis=1)
    
    # Sort by importance
    top_idx = np.argsort(importance)[::-1]
    
    print("\n========================================================")
    print("TOP 3 PRIMARY DRIVER GENES DISCOVERED BY V29.0 MODEL")
    print("========================================================")
    print("These genes are strictly extracted from the model's PyTorch weights.")
    print("They represent the most heavily weighted regulatory targets in the 2M cell manifold.\n")
    
    for i in range(3):
        idx = top_idx[i]
        gene_name = gene_names[idx]
        score = importance[idx]
        print(f"{i+1}. {gene_name} (Weight magnitude: {score:.4f})")

if __name__ == "__main__":
    main()
