with open("index_c4a3865.html", "r", encoding="utf-8") as f:
    c4_content = f.read()

with open("index.html", "r", encoding="utf-8") as f:
    current_content = f.read()

# Check for Developer API Platform in both
print("Is 'Developer API Platform' in index_c4a3865.html?", "Developer API Platform" in c4_content)
print("Is 'Developer API Platform' in current index.html?", "Developer API Platform" in current_content)

# Let's see what other sections are in index_c4a3865.html but not in current index.html
# We can find all elements with ID or sections
import re
id_re = re.compile(r'id=["\']([^"\']+)["\']')
c4_ids = set(id_re.findall(c4_content))
current_ids = set(id_re.findall(current_content))

missing_in_current = c4_ids - current_ids
print("\nIDs in c4a3865 but missing in current index.html:")
print(sorted(list(missing_in_current)))
