import os, glob, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

target_pages = [
    'evidence.html', 'how_it_works.html', 'scientific_qna.html', 'technical_catalog.html',
    'legal.html', 'whitepaper.html', 'discovery_mockup.html', 'contact.html', 'structure.html',
    'regulatory.html', 'trials.html', 'v26_clinical_report.html', 'v30_clinical_report.html',
    'APOLLO_INTRO_DECK.html', 'APOLLO_MEETING_PREP_DECK.html'
]

for fname in target_pages:
    fp = os.path.join(base, fname)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Search for logo or brand elements
    matches = re.findall(r'(<[^>]*class="[^"]*(?:brand|logo)[^"]*"[^>]*>[\s\S]{0,300}?</[^>]+>)', content, re.IGNORECASE)
    print(f"=== {fname} ===")
    if matches:
        for m in matches[:3]:
            print("  - Match:", m.replace('\n', ' ')[:150])
    else:
        # try searching for NILUS or logo text
        lines = content.split('\n')
        for i, l in enumerate(lines[:300]):
            if any(k in l.lower() for k in ['logo', 'brand', 'nav-dock', 'navbar-brand', 'nilus']):
                print(f"  Line {i+1}: {l.strip()[:120]}")
