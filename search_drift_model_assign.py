import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "drift_model =" in line or "drift_model =" in line.replace(" ", ""):
        print(f"Line {idx}: {line.strip()}")
