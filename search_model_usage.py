import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Let's find occurrences of ZenithV2DeepDrift
for match in re.finditer(r'ZenithV2DeepDrift', content):
    start = max(0, match.start() - 200)
    end = min(len(content), match.end() + 200)
    print(f"Match found at position {match.start()}:\n{content[start:end]}\n{'-'*40}")
