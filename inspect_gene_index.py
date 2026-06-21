import json
import os

path = "models/zenith_foundation_v1/gene_index.json"
if os.path.exists(path):
    with open(path, "r") as f:
        data = json.load(f)
    print("Type of data:", type(data))
    if isinstance(data, list):
        print("Length:", len(data))
        print("First 10:", data[:10])
        print("Last 10:", data[-10:])
    elif isinstance(data, dict):
        print("Keys:", list(data.keys())[:10])
        print("Length:", len(data))
else:
    print("File not found")
