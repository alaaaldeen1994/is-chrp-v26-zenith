import re

with open('bridge_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

targets = ['/discovery', '/colony_microscopy_demo', '/evidence', '/regulatory', '/partial-reprogramming', '/robots.txt', '/sitemap.xml', 'index.html']

for i, line in enumerate(lines):
    for t in targets:
        if t in line:
            print(f"Line {i+1}: {line.strip()}")
            # Print next 5 lines
            for j in range(1, 6):
                if i+j < len(lines):
                    print(f"   + {lines[i+j].strip()}")
            print("-" * 50)
            break
