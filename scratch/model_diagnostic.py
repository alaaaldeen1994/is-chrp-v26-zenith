"""
ZENITH MODEL DIAGNOSTIC TOOL
=============================
Inspects ALL models on disk and determines which one the backend actually loads.
"""
import torch
import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

def inspect_model(name, model_dir):
    print(f"\n{'='*60}")
    print(f"MODEL: {name}")
    print(f"PATH:  {os.path.abspath(model_dir)}")
    print(f"{'='*60}")
    
    if not os.path.exists(model_dir):
        print("  STATUS: NOT FOUND")
        return
    
    # List all files
    files = os.listdir(model_dir)
    print(f"  Files: {files}")
    
    # Check for model.pt
    model_pt = os.path.join(model_dir, 'model.pt')
    if os.path.exists(model_pt):
        size_mb = os.path.getsize(model_pt) / (1024*1024)
        print(f"  model.pt size: {size_mb:.1f} MB")
        
        # Load and inspect
        try:
            state = torch.load(model_pt, map_location='cpu', weights_only=False)
            
            if isinstance(state, dict):
                print(f"  Top-level keys: {list(state.keys())}")
                
                # Check for model_state_dict
                if 'model_state_dict' in state:
                    sd = state['model_state_dict']
                    n_params = sum(v.numel() for v in sd.values())
                    print(f"  Total parameters: {n_params:,}")
                    
                    # Find encoder/decoder shapes
                    for key in sd:
                        if 'encoder' in key and 'weight' in key and 'Layer 0' in key:
                            print(f"  Encoder input dim: {sd[key].shape[1]}")
                        if 'px_scale_decoder' in key and 'weight' in key:
                            print(f"  Decoder output (genes): {sd[key].shape[0]}")
                            print(f"  Decoder hidden dim: {sd[key].shape[1]}")
                
                # Check for attr_dict (scVI registry)
                if 'attr_dict' in state:
                    attr = state['attr_dict']
                    if isinstance(attr, str):
                        attr = json.loads(attr)
                    
                    if 'registry_' in attr:
                        reg = attr['registry_']
                        if isinstance(reg, str):
                            reg = json.loads(reg)
                        
                        # Get setup args
                        setup = reg.get('setup_args', {})
                        print(f"  scVI setup_args: {json.dumps(setup, indent=4)[:500]}")
                        
                        # Get field registries to find category mappings
                        field_reg = reg.get('field_registries', {})
                        for field_name, field_data in field_reg.items():
                            sr = field_data.get('state_registry', {})
                            if 'categorical_mapping' in sr:
                                cats = sr['categorical_mapping']
                                if len(cats) <= 20:
                                    print(f"  Registry '{field_name}' categories: {cats}")
                                else:
                                    print(f"  Registry '{field_name}': {len(cats)} categories")
                    
                    if 'n_cells' in attr:
                        print(f"  n_cells (training): {attr['n_cells']}")
                    if 'n_vars' in attr:
                        print(f"  n_vars (genes): {attr['n_vars']}")
                        
            else:
                print(f"  model.pt type: {type(state)}")
                
        except Exception as e:
            print(f"  ERROR loading model.pt: {e}")
    
    # Check for adata.h5ad
    adata_path = os.path.join(model_dir, 'adata.h5ad')
    if os.path.exists(adata_path):
        size_mb = os.path.getsize(adata_path) / (1024*1024)
        print(f"  adata.h5ad size: {size_mb:.1f} MB")
        print(f"  CAN LOAD WITH SCVI: YES (has adata)")
    else:
        print(f"  adata.h5ad: NOT PRESENT")
        print(f"  CAN LOAD WITH SCVI: ONLY if model.pt is self-contained")
    
    # Check for gene_index or var_schema
    for extra in ['gene_index.json', 'var_schema.h5ad']:
        p = os.path.join(model_dir, extra)
        if os.path.exists(p):
            size_mb = os.path.getsize(p) / (1024*1024)
            print(f"  {extra}: {size_mb:.2f} MB")


def main():
    print("="*60)
    print("ZENITH v29 MODEL DIAGNOSTIC REPORT")
    print("="*60)
    
    models = [
        ("zenith_foundation_v1 (Priority 1 - The NEW 2M Model)", 
         os.path.join(MODELS_DIR, 'zenith_foundation_v1')),
        ("scvi_model_hca (Priority 2 - Legacy 18K HCA)", 
         os.path.join(MODELS_DIR, 'scvi_model_hca')),
        ("scvi_model_486k_real (The 486K Cell Model)", 
         os.path.join(MODELS_DIR, 'scvi_model_486k_real')),
        ("zenith_foundation_v1_old (Previous Foundation)", 
         os.path.join(MODELS_DIR, 'zenith_foundation_v1_old')),
    ]
    
    for name, path in models:
        inspect_model(name, path)
    
    # Now determine what the backend ACTUALLY loads
    print(f"\n\n{'='*60}")
    print("BACKEND LOADING ANALYSIS")
    print(f"{'='*60}")
    
    # Priority 1 check
    p1_dir = os.path.join(MODELS_DIR, 'zenith_foundation_v1')
    p1_pt = os.path.join(p1_dir, 'model.pt')
    p1_adata = os.path.join(p1_dir, 'adata.h5ad')
    
    if os.path.exists(p1_pt):
        print("\n[Priority 1] zenith_foundation_v1/model.pt EXISTS")
        print("  Backend calls: SCVI.load(model_dir_486k)  # no adata argument")
        print("  This means scVI tries to load WITHOUT external adata.")
        
        if os.path.exists(p1_adata):
            print("  adata.h5ad IS present -> scVI should load successfully!")
        else:
            print("  adata.h5ad is MISSING -> scVI will FAIL!")
            print("  The model.pt must be fully self-contained for this to work.")
            print("")
            print("  DIAGNOSIS: Priority 1 FAILS. Backend falls through to Priority 2.")
    
    # Priority 2 check  
    p2_dir = os.path.join(MODELS_DIR, 'zenith_foundation_v1')
    p2_adata = os.path.join(p2_dir, 'adata.h5ad')
    
    print(f"\n[Priority 2] Same directory: zenith_foundation_v1")
    print(f"  Backend calls: SCVI.load(model_dir_hca, adata=loaded_adata)")
    print(f"  adata path checked: {p2_adata}")
    
    if os.path.exists(p2_adata):
        print("  adata.h5ad EXISTS -> This path should work!")
    else:
        print("  adata.h5ad MISSING -> This path also FAILS!")
        print("")
        print("  CRITICAL: BOTH Priority 1 AND Priority 2 point to the SAME directory!")
        print("  Neither can load because adata.h5ad is missing from zenith_foundation_v1/")
        print("")
        print("  BUT scvi_model_hca/ HAS adata.h5ad (193 MB)!")
        print("  THE FIX: Priority 2 should point to 'scvi_model_hca' instead of 'zenith_foundation_v1'")

if __name__ == '__main__':
    main()
