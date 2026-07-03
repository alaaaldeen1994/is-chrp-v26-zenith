import re

with open("discovery.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

id_re = re.compile(r'id=["\']([^"\']+)["\']')
ids = set()
for line in lines:
    ids.update(id_re.findall(line))

print(f"discovery.html lines: {len(lines)}")
# Check if some of those missing IDs from old index are in discovery.html
target_ids = ['view-discovery', 'view-simulation', 'viewport-container', 'canvas', 'ai-panel']
for tid in target_ids:
    print(f"Is '{tid}' in discovery.html? {tid in ids}")
