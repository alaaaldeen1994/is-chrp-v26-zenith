import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "driftmlp.pt" in line or "load_state_dict" in line:
        print(f"Line {idx}: {line.strip()}")
        # print the next 20 lines
        for j in range(max(0, idx - 10), min(idx + 30, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
        print("-" * 50)
