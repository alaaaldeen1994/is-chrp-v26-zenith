import re
import os

with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Let's find occurrences of batch.genes
for match in re.finditer(r'batch\.genes', content):
    start = max(0, match.start() - 100)
    end = min(len(content), match.end() + 100)
    print(f"Match found at position {match.start()}:\n{content[start:end]}\n{'-'*40}")
