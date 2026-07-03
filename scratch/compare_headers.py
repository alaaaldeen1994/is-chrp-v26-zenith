with open("index_backup_9688caa.html", "r", encoding="utf-8") as f:
    old_content = f.read()

with open("index.html", "r", encoding="utf-8") as f:
    new_content = f.read()

import re
header_pattern = re.compile(r'<h[1-6][^>]*>(.*?)</h[1-6]>', re.IGNORECASE)

old_headers = header_pattern.findall(old_content)
new_headers = header_pattern.findall(new_content)

print(f"Old headers ({len(old_headers)}):")
for h in old_headers[:30]:
    print("  ", h.strip())

print(f"\nNew headers ({len(new_headers)}):")
for h in new_headers[:30]:
    print("  ", h.strip())
