import numpy as np
data = np.load("data/trajectories/trajectory_pairs.npz", allow_pickle=True)
print(f"Keys: {list(data.keys())}")
print(f"Shape X: {data['X'].shape}")
print(f"Shape Y: {data['Y'].shape}")
