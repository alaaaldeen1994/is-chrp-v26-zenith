import re

with open("js/script.js", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "a.genes" in line or "agent.genes" in line or "payload.genes" in line:
            print(f"Line {idx}: {line.strip()}")
