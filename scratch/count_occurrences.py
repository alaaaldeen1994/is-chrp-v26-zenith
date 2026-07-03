import os
import re

files_to_check = [
    "3d_view.html", "about.html", "api.html", "colony_microscopy_demo.html", 
    "contact.html", "discovery.html", "evidence.html", "how_it_works.html", 
    "index.html", "legal.html", "login.html", "regulatory.html", 
    "scientific_qna.html", "structure.html", "technical_catalog.html", 
    "trials.html", "whitepaper.html", "js/auth_handler.js", "js/script.js",
    "bridge_server.py"
]

print("Checking occurrences:")
for fpath in files_to_check:
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    disc_count = content.count("discovery.html")
    idx_count = content.count("index.html")
    if disc_count > 0 or idx_count > 0:
        print(f"  {fpath}: discovery.html = {disc_count}, index.html = {idx_count}")
