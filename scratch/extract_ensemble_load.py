import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
server_path = os.path.join(base_dir, "bridge_server.py")

with open(server_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\scratch\ensemble_load_code.py"
with open(out_path, 'w', encoding='utf-8') as f:
    for idx in range(1379, min(len(lines), 1530)):
        f.write(f"L{idx+1}: {lines[idx]}")

print("Extracted lines 1380 to 1530 to scratch/ensemble_load_code.py")
