import torch
import scanpy as sc

state_dict = torch.load('models/zenith_foundation_v1/model.pt', map_location='cpu', weights_only=False)

print("Loaded PyTorch Model.")
# Check if it's an scVI save (which is a dict with 'model_state_dict')
if 'model_state_dict' in state_dict:
    state_dict = state_dict['model_state_dict']

print("Keys ending in weight and their shapes:")
for key, tensor in state_dict.items():
    if 'weight' in key and 'decoder' in key:
        print(f"{key}: {tensor.shape}")
