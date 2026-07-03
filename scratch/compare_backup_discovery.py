with open("index_backup_9688caa.html", "r", encoding="utf-8") as f:
    old_content = f.read()

with open("discovery.html", "r", encoding="utf-8") as f:
    disc_content = f.read()

import re
id_re = re.compile(r'id=["\']([^"\']+)["\']')
old_ids = set(id_re.findall(old_content))
disc_ids = set(id_re.findall(disc_content))

missing_in_disc = old_ids - disc_ids
print("IDs in index_backup_9688caa.html (old simulation dashboard) but missing in discovery.html:")
print(sorted(list(missing_in_disc)))
print(f"Old size: {len(old_content)}, Discovery size: {len(disc_content)}")
