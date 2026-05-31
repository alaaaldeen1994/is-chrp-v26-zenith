import os
import json
import torch
import numpy as np

def generate_index(model_dir):
    print(f"\nProcessing model directory: {model_dir}")
    model_pt = os.path.join(model_dir, "model.pt")
    if not os.path.exists(model_pt):
        print(f"  [Error] model.pt not found in {model_dir}")
        return False
        
    try:
        state = torch.load(model_pt, map_location="cpu", weights_only=False)
        var_names = []
        
        # Method 1: direct var_names key
        if "var_names" in state:
            var_names = list(state["var_names"])
        # Method 2: inside attr_dict
        elif "attr_dict" in state:
            attr = state["attr_dict"]
            if "var_names" in attr:
                var_names = list(attr["var_names"])
            elif "registry_" in attr:
                reg = attr["registry_"]
                if "var_names" in reg:
                    var_names = list(reg["var_names"])
                    
        # Method 3: try loading via scvi SCVI if available
        if not var_names:
            try:
                from scvi.model import SCVI
                model = SCVI.load(model_dir)
                if hasattr(model, 'adata_manager') and model.adata_manager is not None:
                    var_names = list(model.adata_manager.registry.get("var_names", []))
            except Exception as load_err:
                print(f"  [scVI Load Error] {load_err}")
                
        # Method 4: Scan top-level keys for any array of strings
        if not var_names:
            for key, val in state.items():
                if isinstance(val, (list, np.ndarray)) and len(val) > 100:
                    sample = val[:5] if isinstance(val, list) else val[:5].tolist()
                    if all(isinstance(s, str) for s in sample):
                        var_names = list(val)
                        print(f"  Found gene names under key: '{key}' ({len(var_names)} genes)")
                        break
                        
        if not var_names:
            print("  [Error] Could not extract gene vocabulary.")
            return False
            
        print(f"  Extracted {len(var_names)} genes.")
        
        # Key markers mapping
        key_genes = [
            "POU5F1", "SOX2", "KLF4", "MYC", "TNNT2", "TTN", "PECAM1",
            "COL1A1", "CD68", "GATA4", "TBX5", "MEF2C", "MYH6", "RYR2",
            "SIRT1", "FOXO3", "TP53", "VWF", "DCN", "CD3D", "NKX2-5",
            "ACTN2", "SCN5A", "MYH7", "NANOG", "LIN28A"
        ]
        
        gene_index = {}
        for g in key_genes:
            g_upper = g.upper()
            var_names_upper = [vn.upper() for vn in var_names]
            if g_upper in var_names_upper:
                gene_index[g] = var_names_upper.index(g_upper)
                
        out_path = os.path.join(model_dir, "gene_index.json")
        with open(out_path, "w") as f:
            json.dump({"var_names": var_names, "key_markers": gene_index}, f)
        print(f"  [OK] Saved gene_index.json -> {out_path}")
        return True
    except Exception as e:
        print(f"  [Error] Failed to process {model_dir}: {e}")
        return False

project_root = "C:\\Users\\alaaa\\.gemini\\antigravity\\scratch\\is-chrp-v26-generative"
models_dir = os.path.join(project_root, "models")
for sub in os.listdir(models_dir):
    sub_path = os.path.join(models_dir, sub)
    if os.path.isdir(sub_path) and os.path.exists(os.path.join(sub_path, "model.pt")):
        generate_index(sub_path)
