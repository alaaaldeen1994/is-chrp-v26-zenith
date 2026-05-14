import psutil
import torch

mem = psutil.virtual_memory()
print(f"System Total Memory: {mem.total / (1024**3):.2f} GB")
print(f"System Available Memory: {mem.available / (1024**3):.2f} GB")
print(f"System Percent Used: {mem.percent}%")

if torch.cuda.is_available():
    print(f"GPU Available: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory Total: {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
else:
    print("No GPU detected.")
