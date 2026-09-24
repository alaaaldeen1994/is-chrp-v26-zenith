import os
import glob
import re

print("Checking existence of referenced files:")
checks = [
    "v31_clinical_report.html",
    "v30_clinical_report.html",
    "v26_clinical_report.html",
    "colony_microscopy_demo.html",
    "evidence.html",
    "regulatory.html",
    "trials.html",
    "whitepaper.html",
    "technical_catalog.html",
    "profile.html",
    "about.html",
    "contact.html",
    "structure.html",
    "scientific_qna.html",
    "legal.html",
    "how_it_works.html",
    "zenith_scientific_paper.html",
    "paper.html",
    "paper.pdf",
    "zenith_scientific_paper.pdf",
    "discovery.html"
]

for c in checks:
    exists = os.path.exists(c)
    print(f"  {c:30} -> Exists: {exists}")

# Check for ${pubmed} in HTML files
print("\nChecking for ${pubmed} or unrendered variables in HTML files:")
for fpath in glob.glob("*.html"):
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    matches = re.findall(r'href=[\'"](\$\{[^\}]+\})[\'"]', content)
    if matches:
        print(f"  In {fpath}: {matches}")
