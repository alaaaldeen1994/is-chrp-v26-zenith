
import torch
from bridge_server import ZenithV2DeepDrift

# Initialize the model with the production dimensions
model = ZenithV2DeepDrift(input_dim=5000, hidden_dim=2048, depth=12)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

print(f"\n--- ZENITH ULTRA DATA SHEET ---")
print(f"Total Parameters:    {total_params:,}")
print(f"Trainable Params:    {trainable_params:,}")
print(f"Model Architecture:  Transformer (Zenith Ultra)")
print(f"Input Vocabulary:    5,000 Genes")
print("--------------------------------\n")
