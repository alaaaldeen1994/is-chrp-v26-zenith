import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "class BatchCellState" in line or "class BatchSimulationResult" in line:
        print(f"Line {idx}: {line.strip()}")
        # print the next 20 lines
        for j in range(idx, min(idx + 25, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
