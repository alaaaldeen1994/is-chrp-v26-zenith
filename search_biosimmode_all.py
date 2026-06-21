import os
import re

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".js", ".html")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "biosimmode" in content.lower():
                print(f"Found in {path}")
                for idx, line in enumerate(content.splitlines(), 1):
                    if "biosimmode" in line.lower():
                        print(f"  Line {idx}: {line.strip()}")
