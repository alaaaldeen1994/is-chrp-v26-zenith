import json
import os

path = "models/zenith_foundation_v1/gene_index.json"
if os.path.exists(path):
    with open(path, "r") as f:
        data = json.load(f)
    if "var_names" in data:
        print("Length of var_names:", len(data["var_names"]))
        print("First 15 var_names:", data["var_names"][:15])
    if "key_markers" in data:
        print("key_markers:", data["key_markers"])
else:
    print("File not found")
