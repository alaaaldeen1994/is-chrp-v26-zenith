import json

with open("models/cell_type_genes.json", "r") as f:
    data = json.load(f)

print("Keys:", data.keys())
if "cell_types" in data:
    print("Cell types inside:", data["cell_types"].keys())
    # print the first cell type keys
    first_ct = list(data["cell_types"].keys())[0]
    print(f"Keys of cell type '{first_ct}':", data["cell_types"][first_ct].keys())
    if "pro_rejuvenation_genes" in data["cell_types"][first_ct]:
        print(f"Number of pro-rejuvenation genes: {len(data['cell_types'][first_ct]['pro_rejuvenation_genes'])}")
    if "aging_marker_genes" in data["cell_types"][first_ct]:
        print(f"Number of aging marker genes: {len(data['cell_types'][first_ct]['aging_marker_genes'])}")
