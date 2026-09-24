import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
html_files = glob.glob(os.path.join(base, '*.html'))

for filepath in sorted(html_files):
    fname = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find any svg+NILUS, data-lucide="layers", or nav logo patterns
    matches = re.findall(r'(<div[^>]*class="[^"]*flex[^"]*"[^>]*>\s*<(?:svg|i)[^>]*>[\s\S]{0,300}?</span\s*>\s*</span\s*>\s*</div\s*>\s*</div\s*>)', content, re.IGNORECASE)
    
    # Or simpler: find any element containing NILUS and LAB inside a nav/header
    nilus_matches = re.findall(r'([^<]*NILUS[^<]*LAB[^<]*)', content)
    
    print(f"=== {fname} ===")
    if 'data:image/png;base64,' in content:
        print("  Already has base64 logo!")
    else:
        # Search for lines around NILUS LAB or nav
        lines = content.split('\n')
        found = False
        for i, line in enumerate(lines):
            if 'NILUS' in line and 'LAB' in line and ('span' in line or 'div' in line or 'a' in line):
                print(f"  Line {i+1}: {line.strip()[:140]}")
                found = True
        if not found:
            # check for svg / layers
            for i, line in enumerate(lines):
                if ('lucide="layers"' in line or '<nav' in line or 'class="nav' in line) and i < 350:
                    print(f"  Line {i+1}: {line.strip()[:140]}")
