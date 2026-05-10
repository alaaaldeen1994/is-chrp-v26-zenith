import os

def fix_nav():
    path = 'profile.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    target = """                        <a href="v27_clinical_report.html">Clinical Report v27.0 GOLD</a>
                    </div>"""
    
    replacement = """                        <a href="v27_clinical_report.html">Clinical Report v27.0 GOLD</a>
                        <a href="how_it_works.html" style="color: #2563eb; font-weight: 800;">A-Z Operational Manual</a>
                    </div>"""
    
    if target in content:
        new_content = content.replace(target, replacement)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Updated navigation in profile.html")
    else:
        # Fuzzy match
        import re
        pattern = r'<a href="v27_clinical_report\.html">Clinical Report v27\.0 GOLD</a>\s+</div>'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
            print("Updated navigation in profile.html (Fuzzy Match)")
        else:
            print("Target not found in profile.html")

if __name__ == "__main__":
    fix_nav()
