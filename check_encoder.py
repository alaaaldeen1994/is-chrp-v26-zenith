from scvi.model import SCVI
import torch

model = SCVI.load("models/scvi_model_486k")
m = model.module

z = torch.randn(1, 30)
lib = torch.log(torch.tensor([[1e4]]))
batch = torch.zeros(1, 1, dtype=torch.long)

with torch.no_grad():
    out = m.generative(z, lib, batch_index=batch)
    print("Keys:", list(out.keys()))
    for k, v in out.items():
        if hasattr(v, "shape"):
            print(f"  {k}: shape={v.shape}, dtype={v.dtype}")
        else:
            print(f"  {k}: type={type(v).__name__}")
