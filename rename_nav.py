import os
import re

def rename_nav():
    path = 'profile.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Target the specific link I just added
    pattern = r'<a href="how_it_works\.html" style="color: #2563eb; font-weight: 800;">A-Z Operational Manual</a>'
    replacement = r'<a href="how_it_works.html" style="color: #2563eb; font-weight: 800;">How Zenith Works (A-Z)</a>'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Renamed link in profile.html to 'How Zenith Works (A-Z)'")
    else:
        print("Link not found in profile.html for renaming.")

if __name__ == "__main__":
    rename_nav()
