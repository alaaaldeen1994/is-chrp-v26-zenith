import os
import uuid
import numpy as np
import pandas as pd
import anndata as ad
from typing import List, Dict, Any, Optional

def serialize_to_h5ad(
    genes: List[str],
    expression_matrix: np.ndarray,
    latent_coords: Optional[np.ndarray] = None,
    obs_metadata: Optional[List[Dict[str, Any]]] = None,
    output_dir: str = "scratch"
) -> str:
    """
    Serializes simulated cell transcriptomic profiles and metadata into an AnnData (.h5ad) file.
    Returns the absolute path of the generated file.
    """
    # 1. Ensure target directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Check input shapes
    num_cells = expression_matrix.shape[0]
    num_genes = len(genes)
    assert expression_matrix.shape[1] == num_genes, f"Matrix width ({expression_matrix.shape[1]}) must match gene list length ({num_genes})"
    
    # 3. Formulate observations (obs) metadata
    if obs_metadata and len(obs_metadata) == num_cells:
        obs_df = pd.DataFrame(obs_metadata)
    else:
        # Default metadata if empty or mismatched
        obs_df = pd.DataFrame({
            "cell_id": [f"cell_{i}" for i in range(num_cells)],
            "cell_type": ["ventricular_myocyte"] * num_cells,
            "species": ["homo_sapiens"] * num_cells
        })
    obs_df.index = [f"cell_{i}" for i in range(num_cells)]
    
    # 4. Formulate variables (var) metadata
    var_df = pd.DataFrame(index=genes)
    var_df["gene_symbol"] = genes
    
    # 5. Instantiate AnnData
    adata = ad.AnnData(
        X=expression_matrix.astype(np.float32),
        obs=obs_df,
        var=var_df
    )
    
    # 6. Add latent representations (obsm) if provided
    if latent_coords is not None and latent_coords.shape[0] == num_cells:
        adata.obsm["X_umap"] = latent_coords.astype(np.float32)
        
    # 7. Write to physical file
    filename = f"zenith_sim_{uuid.uuid4().hex[:12]}.h5ad"
    filepath = os.path.abspath(os.path.join(output_dir, filename))
    
    adata.write_h5ad(filepath)
    return filepath
