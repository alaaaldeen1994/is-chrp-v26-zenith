"""
fetch_diseased_biopsy.py
~~~~~~~~~~~~~~~~~~~~~~~~
Programmatically download real patient biopsy cells (atherosclerosis or heart failure)
using the CZ CELLxGENE Census API. Extracts only the cell lineage of interest
to prevent massive disk usage.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import scanpy as sc
import cellxgene_census


# 1. Configuration
OUTPUT_DIR = "data/real"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "patient_atherosclerosis_biopsy.h5ad")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("⚡ Connecting to CZ CELLxGENE Census Cloud...")
try:
    with cellxgene_census.open_soma() as census:
        # Define our query filter:
        # We want Human cells (homo_sapiens) from vascular tissue with atherosclerosis disease
        # and specifically targeting smooth muscle cells (the primary drivers of hyper-sclerosis)
        query_filter = (
            "tissue_general == 'blood vessel' and "
            "disease == 'atherosclerosis' and "
            "cell_type == 'smooth muscle cell' and "
            "organism == 'Homo sapiens'"
        )
        
        print("🔍 Querying database for matching patient biopsies...")
        # Stream cell metadata and expression data (subsampling to 5,000 cells to save memory/space)
        adata = cellxgene_census.get_anndata(
            census=census,
            organism="Homo sapiens",
            measurement_name="RNA",
            obs_value_filter=query_filter,
            obs_embeddings=["umap"] # Include UMAP coordinates if available
        )
        
        # Subsample to a highly representative subset if the query is too large
        if adata.n_obs > 5000:
            print(f"📊 Found {adata.n_obs:,} cells. Subsampling to 5,000 cells to optimize local memory...")
            sc.pp.subsample(adata, n_obs=5000, random_state=42)
            
        # Save locally
        adata.write_h5ad(OUTPUT_FILE)
        print(f"✅ SUCCESS! Extracted {adata.n_obs:,} cells x {adata.n_vars:,} genes.")
        print(f"💾 Saved local clinical biopsy file to: {OUTPUT_FILE}")
        
except Exception as e:
    print(f"❌ Error during Census API download: {e}")
    print("💡 Please make sure 'cellxgene-census' is installed: pip install cellxgene-census")
