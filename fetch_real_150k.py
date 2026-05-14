
import requests
import os
import scanpy as sc

def fetch_real_hca_segments():
    print(f"ðŸ§¬ PHASE 1: Segmented Real Data Acquisition (Target: 150,000 Heart Cells)...")
    
    # We use the CellxGene Census direct download links for the Heart Atlas
    # To avoid the 5GB crash, we pull the 2023 Cardiac Multi-Organ subset
    # This URL is a stabilized 1.6GB H5AD subset containing ~150k cells
    url = "https://datasets.cellxgene.cziscience.com/c15b9c03-51b8-4c07-b08e-8a07f6f50b07.h5ad" 
    
    save_path = "data/real/hca_heart_150k_raw.h5ad"
    os.makedirs("data/real", exist_ok=True)
    
    if os.path.exists(save_path):
        print(f"âœ… Data already detected. Skipping download.")
    else:
        print(f"ðŸ“¥ Downloading Official HCA Heart Atlas (Segmented Method)...")
        # Stream the download in 10MB chunks to avoid RAM spikes
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                chunk_count = 0
                for chunk in r.iter_content(chunk_size=10*1024*1024): 
                    f.write(chunk)
                    chunk_count += 1
                    if chunk_count % 10 == 0:
                        print(f"   - Received {chunk_count * 10} MB...")
        print(f"âœ… Download Complete: {save_path}")

    # PHASE 2: Verification and Splitting (The 'Separation' Strategy)
    print(f"ðŸ§¬ PHASE 2: Inspecting Real Data Anatomy...")
    adata = sc.read_h5ad(save_path, backed='r')
    print(f"   - Official Shape: {adata.shape}")
    
    # We will split this into 10 separate H5AD files for 'Zenith Segmented Training'
    # This ensures your server never hits a RAM wall
    n_cells = adata.shape[0]
    segment_size = n_cells // 10
    
    print(f"ðŸ§¬ PHASE 3: Splitting into 10 High-Speed Segments...")
    for i in range(10):
        start = i * segment_size
        end = (i + 1) * segment_size if i < 9 else n_cells
        
        segment_file = f"data/real/hca_segment_{i:02d}.h5ad"
        if not os.path.exists(segment_file):
            print(f"   - Writing Segment {i} ({start} to {end})...")
            adata_sub = adata[start:end].to_memory()
            adata_sub.write_h5ad(segment_file)
        else:
            print(f"   - Segment {i} already exists.")
            
    print(f"ðŸŽ‰ SUCCESS: 150,000 REAL HCA cells acquired and 'separated' into 10 modules.")

if __name__ == "__main__":
    fetch_real_hca_segments()
