import os
import json

centroids_path = os.path.join(os.path.dirname(__file__), "..", "models", "real_centroids.json")
if os.path.exists(centroids_path):
    with open(centroids_path) as f:
        ct = json.load(f)
    print("Keys in real_centroids.json:", ct.keys())
    for k in ct.keys():
        if isinstance(ct[k], dict):
            print(f"Keys in ct['{k}'].keys():", ct[k].keys())
            if "centroid" in ct[k]:
                import numpy as np
                arr = np.array(ct[k]["centroid"])
                print(f"  Shape of ct['{k}']['centroid']:", arr.shape)
else:
    print("ERROR: File does not exist.")
