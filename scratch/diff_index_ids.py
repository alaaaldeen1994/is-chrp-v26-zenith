import difflib
import sys

with open("index_backup_9688caa.html", "r", encoding="utf-8") as f:
    old_lines = f.readlines()

with open("index.html", "r", encoding="utf-8") as f:
    new_lines = f.readlines()

print(f"Old lines: {len(old_lines)}, New lines: {len(new_lines)}")

# Let's find some big blocks that are present in old but not in new
# Or write a summary of missing divs or sections
# Let's count tags or print text blocks that are missing
old_headers = [line.strip() for line in old_lines if line.strip().startswith("<h") or "id=" in line]
new_headers = [line.strip() for line in new_lines if line.strip().startswith("<h") or "id=" in line]

print("\n--- IDs in Old file not in New file ---")
import re
id_re = re.compile(r'id=["\']([^"\']+)["\']')
old_ids = set()
for line in old_lines:
    old_ids.update(id_re.findall(line))

new_ids = set()
for line in new_lines:
    new_ids.update(id_re.findall(line))

missing_ids = old_ids - new_ids
print(sorted(list(missing_ids)))

print("\n--- IDs in New file not in Old file ---")
added_ids = new_ids - old_ids
print(sorted(list(added_ids)))
