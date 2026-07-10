import os
import re

BASE = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"

TARGET_FILES = [
    "index.html",
    "profile.html",
    "technical_catalog.html",
    "whitepaper.html",
    "v26_clinical_report.html",
    "v30_clinical_report.html",
    "api.html",
    "structure.html",
    "trials.html",
    "evidence.html",
    "discovery_mockup.html",
    "colony_microscopy_demo.html",
    "pilot_dashboard.html",
    "how_it_works.html",
    "regulatory.html",
    "legal.html",
    "login.html",
    "about.html",
    "contact.html",
    "scientific_qna.html",
    "3d_view.html",
    "NILUS_MASTER_PITCH_V2.html",
    "NILUS_LAB_INVESTOR_MASTER.html",
    "NILUS_PITCH_DECK.html",
    "INVESTOR_PITCH_WAED.html",
    "APOLLO_INTRO_DECK.html",
    "APOLLO_MEETING_PREP_DECK.html",
    "APOLLO_SCRIPT.html",
    "ZENITH_PHASE_A_ACADEMIC_POSTER.html",
    "ZENITH_PHASE_A_EXECUTIVE_PITCH.html",
    "REAL_ACADEMIC_POSTER_A0.html",
]

# Hex teal/cyan replacements → blue equivalents
HEX_REPLACEMENTS = [
    ("#0d9488", "#1d4ed8"),   # teal-600 → blue-700
    ("#14b8a6", "#2563eb"),   # teal-500 → blue-600
    ("#0f766e", "#1e40af"),   # teal-700 → blue-800
    ("#115e59", "#1e3a8a"),   # teal-800 → blue-900
    ("#134e4a", "#1e3a8a"),   # teal-900 → blue-900
    ("#99f6e4", "#bfdbfe"),   # teal-200 → blue-200
    ("#ccfbf1", "#dbeafe"),   # teal-100 → blue-100
    ("#f0fdfa", "#eff6ff"),   # teal-50  → blue-50
    ("#5eead4", "#60a5fa"),   # teal-300 → blue-400
    ("#2dd4bf", "#3b82f6"),   # teal-400 → blue-500
]

# Tailwind teal-* class replacements
TAILWIND_REPLACEMENTS = [
    ("teal-900", "blue-900"),
    ("teal-800", "blue-800"),
    ("teal-700", "blue-700"),
    ("teal-600", "blue-600"),
    ("teal-500", "blue-500"),
    ("teal-400", "blue-400"),
    ("teal-300", "blue-300"),
    ("teal-200", "blue-200"),
    ("teal-100", "blue-100"),
    ("teal-50",  "blue-50"),
    # CSS variable names
    ("--zenith-teal", "--zenith-blue"),
    ("zenith-teal",   "zenith-blue"),
]

total_changes = 0

for filename in TARGET_FILES:
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        continue

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content
    file_changes = 0

    for old, new in HEX_REPLACEMENTS:
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        new_content, n = pattern.subn(new, content)
        if n > 0:
            file_changes += n
            content = new_content

    for old, new in TAILWIND_REPLACEMENTS:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            file_changes += count

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[FIXED]  {filename} - {file_changes} replacement(s)")
        total_changes += file_changes
    else:
        print(f"[CLEAN]  {filename}")

print(f"\nDone. Total: {total_changes} replacements")
