# -*- coding: utf-8 -*-
"""
Download Human Heart Cell Atlas - 486,134 REAL cells
Uses CellxGene presigned URL API.
"""
import sys, os, json, time, requests

sys.stdout.reconfigure(encoding='utf-8')
def p(msg): print(msg, flush=True)

API = "https://api.cellxgene.cziscience.com"
DATASET_ID = "a7f6822d-0e0e-451e-9858-af81392fcb9b"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "hca_full")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(DATA_DIR, "heart_adult_full.h5ad")

p("=" * 60)
p("HEART CELL ATLAS DOWNLOAD")
p("Target: 486,134 real human cardiac cells")
p("=" * 60)

if os.path.exists(OUTPUT_PATH):
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    p(f"\nAlready downloaded: {size_mb:.1f} MB")
    import scanpy as sc
    adata = sc.read_h5ad(OUTPUT_PATH)
    p(f"REAL CELLS: {adata.n_obs:,}")
    sys.exit(0)

# Step 1: Get the H5AD asset ID
p("\n[1] Finding H5AD asset...")
r = requests.get(f"{API}/dp/v1/datasets/{DATASET_ID}/assets", timeout=30)
assets_data = r.json()
assets = assets_data.get('assets', assets_data) if isinstance(assets_data, dict) else assets_data

h5ad_asset_id = None
for asset in assets:
    if isinstance(asset, dict) and asset.get('filetype') == 'H5AD':
        h5ad_asset_id = asset['id']
        p(f"  H5AD Asset ID: {h5ad_asset_id}")
        p(f"  S3 URI: {asset.get('s3_uri', 'N/A')}")
        break

if not h5ad_asset_id:
    p("  No H5AD found, trying RAW_H5AD...")
    for asset in assets:
        if isinstance(asset, dict) and asset.get('filetype') == 'RAW_H5AD':
            h5ad_asset_id = asset['id']
            p(f"  RAW_H5AD Asset ID: {h5ad_asset_id}")
            break

if not h5ad_asset_id:
    p("ERROR: No H5AD asset found!")
    p(f"  Assets: {json.dumps(assets_data, indent=2)[:500]}")
    sys.exit(1)

# Step 2: Get presigned download URL
p("\n[2] Getting presigned URL...")
r = requests.post(
    f"{API}/dp/v1/datasets/{DATASET_ID}/asset/{h5ad_asset_id}",
    timeout=30
)
p(f"  Status: {r.status_code}")

if r.status_code != 200:
    p(f"  Response: {r.text[:300]}")
    
    # Fallback: Try direct S3 URL (public bucket)
    p("\n  Trying direct S3 download...")
    s3_url = f"https://corpora-data-prod.s3.amazonaws.com/{DATASET_ID}/local.h5ad"
    p(f"  URL: {s3_url}")
    
    try:
        r = requests.head(s3_url, timeout=10)
        p(f"  HEAD status: {r.status_code}")
        if r.status_code == 200:
            download_url = s3_url
        elif r.status_code == 403:
            # Try the datasets.cellxgene.cziscience.com pattern
            alt_url = f"https://datasets.cellxgene.cziscience.com/{DATASET_ID}.h5ad"
            p(f"\n  Trying: {alt_url}")
            r2 = requests.head(alt_url, timeout=10, allow_redirects=True)
            p(f"  HEAD status: {r2.status_code}")
            if r2.status_code == 200:
                download_url = alt_url
            else:
                p(f"  All direct URLs failed")
                sys.exit(1)
        else:
            p(f"  Direct S3 failed")
            sys.exit(1)
    except Exception as e:
        p(f"  Error: {e}")
        sys.exit(1)
else:
    resp_data = r.json()
    download_url = resp_data.get('presigned_url', resp_data.get('url'))
    p(f"  Got presigned URL!")

# Step 3: Download
p(f"\n[3] Downloading H5AD file...")

try:
    r = requests.get(download_url, stream=True, timeout=1200)
    r.raise_for_status()
    
    total = int(r.headers.get('content-length', 0))
    p(f"  File size: {total / (1024*1024):.0f} MB")
    
    downloaded = 0
    t0 = time.time()
    
    with open(OUTPUT_PATH, 'wb') as f:
        for chunk in r.iter_content(chunk_size=131072):
            f.write(chunk)
            downloaded += len(chunk)
            
            elapsed = time.time() - t0
            if downloaded % (25 * 1024 * 1024) < 131072:
                speed = downloaded / (1024 * 1024 * max(elapsed, 0.01))
                if total > 0:
                    pct = 100 * downloaded / total
                    p(f"  {pct:.0f}% - {downloaded // (1024*1024)} MB - {speed:.1f} MB/s")
                else:
                    p(f"  {downloaded // (1024*1024)} MB - {speed:.1f} MB/s")
    
    final_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    elapsed = time.time() - t0
    p(f"\n  COMPLETE: {final_mb:.0f} MB in {elapsed:.0f}s")

except Exception as e:
    p(f"  DOWNLOAD ERROR: {e}")
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
    sys.exit(1)

# Step 4: Verify
p(f"\n[4] Verifying...")
import scanpy as sc
adata = sc.read_h5ad(OUTPUT_PATH)

p(f"  CELLS: {adata.n_obs:,}")
p(f"  GENES: {adata.n_vars:,}")

yamanaka = ['POU5F1', 'SOX2', 'NANOG', 'KLF4', 'MYC', 'LIN28A']
found = [g for g in yamanaka if g in adata.var_names]
p(f"  Yamanaka factors: {len(found)}/6 ({found})")

if 'cell_type' in adata.obs.columns:
    p(f"\n  Cell Types:")
    for ct, n in adata.obs['cell_type'].value_counts().items():
        p(f"    {ct}: {n:,}")

# Save audit
audit = {
    "source": "CellxGene Discover",
    "dataset": "Cells of the adult human heart (Litvinukova 2020)",
    "dataset_id": DATASET_ID,
    "real_cells": int(adata.n_obs),
    "genes": int(adata.n_vars),
    "yamanaka_found": found,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
}

audit_path = os.path.join(DATA_DIR, "cell_audit.json")
with open(audit_path, 'w') as f:
    json.dump(audit, f, indent=2)

p(f"\n" + "=" * 60)
p(f"VERIFIED: {adata.n_obs:,} REAL HUMAN CARDIAC CELLS")
p(f"=" * 60)
