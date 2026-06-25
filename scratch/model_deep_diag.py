"""Quick extract of attr_dict from each model to see n_cells, n_vars, registry"""
import torch, json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

models = {
    "zenith_foundation_v1 (NEW 159MB)": "zenith_foundation_v1",
    "scvi_model_hca (LEGACY 66MB)": "scvi_model_hca", 
    "scvi_model_486k_real (486K 13MB)": "scvi_model_486k_real",
    "zenith_foundation_v1_old (OLD 52MB)": "zenith_foundation_v1_old",
}

for label, folder in models.items():
    pt = os.path.join(MODELS_DIR, folder, 'model.pt')
    if not os.path.exists(pt):
        continue
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")
    
    state = torch.load(pt, map_location='cpu', weights_only=False)
    
    # Count params properly
    sd = state.get('model_state_dict', {})
    total = 0
    for k, v in sd.items():
        if hasattr(v, 'numel'):
            total += v.numel()
    print(f"  Parameters: {total:,}")
    
    # Get decoder output shape (= number of genes)
    for k, v in sd.items():
        if 'px_scale_decoder' in k and 'weight' in k:
            print(f"  Output genes: {v.shape[0]}")
            break
    
    # Extract attr_dict
    attr = state.get('attr_dict', '{}')
    if isinstance(attr, str):
        attr = json.loads(attr)
    
    print(f"  n_cells (trained on): {attr.get('n_cells', 'N/A')}")
    print(f"  n_vars (genes):       {attr.get('n_vars', 'N/A')}")
    
    # Check registry
    reg = attr.get('registry_', {})
    if isinstance(reg, str):
        reg = json.loads(reg)
    
    field_reg = reg.get('field_registries', {})
    for fname, fdata in field_reg.items():
        sr = fdata.get('state_registry', {})
        cats = sr.get('categorical_mapping', [])
        if len(cats) > 0 and len(cats) <= 30:
            cats_list = cats.tolist() if hasattr(cats, 'tolist') else list(cats)
            print(f"  Field '{fname}': {len(cats)} categories -> {cats_list[:10]}")
        elif len(cats) > 0:
            print(f"  Field '{fname}': {len(cats)} categories")
    
    # var_names
    vn = state.get('var_names', [])
    if hasattr(vn, 'tolist'):
        vn = vn.tolist()
    print(f"  var_names count: {len(vn)}")
    if len(vn) > 0:
        print(f"  First 5 genes: {vn[:5]}")
        print(f"  Last 5 genes:  {vn[-5:]}")

print(f"\n\n{'='*60}")
print("CONCLUSION")
print(f"{'='*60}")
print("""
WHAT HAPPENS WHEN bridge_server.py STARTS:

1. Priority 1: It tries SCVI.load('models/zenith_foundation_v1')
   - model.pt is 159MB and EXISTS
   - BUT adata.h5ad is MISSING from that folder  
   - scVI needs either a self-contained model.pt OR an external adata
   - RESULT: FAILS with registry error -> falls to Priority 2

2. Priority 2: It tries SCVI.load('models/zenith_foundation_v1', adata=...)
   - It looks for adata.h5ad in THE SAME FOLDER (zenith_foundation_v1)
   - adata.h5ad is still MISSING there!
   - RESULT: ALSO FAILS -> falls to Priority 3 (NONE)

3. The REAL adata.h5ad (193MB) is sitting in models/scvi_model_hca/
   But the code never points there!

FIX: Change Priority 2 to point model_dir_hca -> 'scvi_model_hca'
     so it can load the legacy 18K model as a working fallback.
     OR: Copy scvi_model_hca/adata.h5ad into zenith_foundation_v1/
""")
