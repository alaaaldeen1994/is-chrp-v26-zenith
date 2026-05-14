import json
with open("models/scvi_model_486k/gene_index.json", "r") as f:
    data = json.load(f)
    var_names = data["var_names"]
    key_markers = data["key_markers"]
    
    for symbol, idx in key_markers.items():
        print(f"{symbol} -> Index {idx} -> var_name: {var_names[idx]}")
