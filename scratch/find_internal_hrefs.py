import glob
import re

html_files = glob.glob("*.html")
all_hrefs = set()
href_sources = {}

for fpath in html_files:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    hrefs = re.findall(r'href=[\'"]([^\'\"#][^\'\"]*)[\'"]', content)
    for h in hrefs:
        if not h.startswith("http") and not h.startswith("mailto:") and not h.startswith("javascript:"):
            all_hrefs.add(h)
            href_sources.setdefault(h, []).append(fpath)

print(f"Total unique internal href links: {len(all_hrefs)}")
print("\n--- INTERNAL LINKS FOUND IN HTML FILES ---")
for h in sorted(all_hrefs):
    sources = href_sources[h]
    print(f"{h:40} (in {len(sources)} files: {', '.join(sources[:3])})")
