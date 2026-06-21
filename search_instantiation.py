import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

for match in re.finditer(r'ZenithV2DeepDrift\(', content):
    start = max(0, match.start() - 150)
    end = min(len(content), match.end() + 150)
    print(f"Match found at position {match.start()}:\n{content[start:end]}\n{'-'*40}")
