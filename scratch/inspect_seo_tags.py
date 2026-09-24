import os
import glob
import re

html_files = glob.glob("*.html")
print(f"Found {len(html_files)} HTML files in root:")

for fpath in sorted(html_files):
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "NO TITLE"
    
    canonical_match = re.search(r'<link[^>]+rel=[\'"]canonical[\'"][^>]*>', content, re.IGNORECASE)
    canonical = canonical_match.group(0) if canonical_match else "MISSING CANONICAL"
    
    robots_meta = re.search(r'<meta[^>]+name=[\'"]robots[\'"][^>]*>', content, re.IGNORECASE)
    robots = robots_meta.group(0) if robots_meta else "NO ROBOTS META"
    
    print(f"\n[{fpath}]")
    print(f"  Title: {title[:60]}")
    print(f"  Canonical: {canonical}")
    print(f"  Robots Meta: {robots}")
