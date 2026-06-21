import os
import json
import numpy as np

centroids_path = os.path.join(os.path.dirname(__file__), "..", "models", "real_centroids.json")
if os.path.exists(centroids_path):
    with open(centroids_path) as f:
        ct = json.load(f)
    young = np.array(ct["young"]["centroid"])
    aged = np.array(ct["aged"]["centroid"])
    print("Young centroid:", young[:5], "... Mean:", young.mean())
    print("Aged centroid:", aged[:5], "... Mean:", aged.mean())
else:
    print("ERROR: File does not exist.")
