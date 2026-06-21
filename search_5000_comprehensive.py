import os
import re

pattern = re.compile(r'\b5,000\b|\b5000\b')

ignore_dirs = {".git", ".agent", "__pycache__", ".pytest_cache", "node_modules"}

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ignore_dirs]
    for file in files:
        if file.endswith((".py", ".js", ".html", ".json", ".md")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if pattern.search(content):
                    print(f"Found in {path}")
                    for idx, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            print(f"  Line {idx}: {line.strip()}")
            except Exception as e:
                print(f"Error reading {path}: {e}")
