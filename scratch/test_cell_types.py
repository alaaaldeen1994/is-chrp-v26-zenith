import os
import json

path = os.path.join(os.path.dirname(__file__), "..", "models", "cell_type_genes.json")
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
    print("Keys in cell_type_genes.json:", data.keys())
    if "cell_types" in data:
        print("Available cell types and their age deltas:")
        for ct_key, ct_info in data["cell_types"].items():
            print(f"  {ct_key}: label={ct_info.get('cell_type')}, age_delta_years={ct_info.get('age_delta_years')}")
else:
    print("ERROR: File does not exist.")
