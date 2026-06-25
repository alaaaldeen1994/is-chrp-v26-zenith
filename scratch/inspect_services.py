import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\services"
lnp_path = os.path.join(base_dir, "lnp_optimizer.py")
multiomics_path = os.path.join(base_dir, "multiomics_service.py")

print("--- services/lnp_optimizer.py ---")
if os.path.exists(lnp_path):
    with open(lnp_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("lnp_optimizer.py not found")

print("\n--- services/multiomics_service.py ---")
if os.path.exists(multiomics_path):
    with open(multiomics_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("multiomics_service.py not found")
