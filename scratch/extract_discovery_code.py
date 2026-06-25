import os

server_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\bridge_server.py"

with open(server_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract lines from 6650 to 7000 (0-indexed: 6649 to 6999)
start_line = 6650
end_line = 7050

out_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\scratch\gpt_discovery_code.py"
with open(out_path, 'w', encoding='utf-8') as f:
    for idx in range(start_line - 1, min(len(lines), end_line)):
        f.write(f"L{idx+1}: {lines[idx]}")

print(f"Extracted lines {start_line} to {end_line} to scratch/gpt_discovery_code.py")
