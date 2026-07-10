import os
import re

BASE = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"

TARGET_FILES = [
    "index.html",
    "technical_catalog.html",
    "whitepaper.html",
    "NILUS_MASTER_PITCH_V2.html",
    "INVESTOR_PITCH_WAED.html",
    "colony_microscopy_demo.html",
    "discovery_mockup.html",
    "structure.html",
    "trials.html",
    "pilot_dashboard.html",
    "APOLLO_INTRO_DECK.html",
    "APOLLO_MEETING_PREP_DECK.html",
    "APOLLO_SCRIPT.html",
    "NILUS_PITCH_DECK.html",
    "NILUS_LAB_INVESTOR_MASTER.html",
    "v26_clinical_report.html",
    "v30_clinical_report.html",
]

# Exact hex replacements
HEX_REPLACEMENTS = [
    ("#059669", "#1d4ed8"),
    ("#047857", "#1e40af"),
    ("#10b981", "#2563eb"),
    ("#34d399", "#60a5fa"),
    ("#6ee7b7", "#93c5fd"),
    ("#a7f3d0", "#bfdbfe"),
    ("#d1fae5", "#dbeafe"),
    ("#ecfdf5", "#eff6ff"),
    ("#065f46", "#1e3a8a"),
    ("#064e3b", "#1e3a8a"),
]

# Tailwind class replacements (word-boundary safe)
TAILWIND_REPLACEMENTS = [
    ("emerald-900", "blue-900"),
    ("emerald-800", "blue-800"),
    ("emerald-700", "blue-700"),
    ("emerald-600", "blue-600"),
    ("emerald-500", "blue-500"),
    ("emerald-400", "blue-400"),
    ("emerald-300", "blue-300"),
    ("emerald-200", "blue-200"),
    ("emerald-100", "blue-100"),
    ("emerald-50",  "blue-50"),
    # green- classes (but NOT 'background', 'foreground' etc.)
    ("green-900", "slate-900"),
    ("green-800", "slate-800"),
    ("green-700", "blue-700"),
    ("green-600", "blue-600"),
    ("green-500", "blue-500"),
    ("green-400", "blue-400"),
    ("green-300", "blue-300"),
    ("green-200", "blue-200"),
    ("green-100", "blue-100"),
    ("green-50",  "blue-50"),
]

total_changes = 0

for filename in TARGET_FILES:
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print(f"[SKIP] {filename} — not found")
        continue

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    original = content
    file_changes = 0

    # Hex replacements (case-insensitive)
    for old, new in HEX_REPLACEMENTS:
        pattern = re.compile(re.escape(old), re.IGNORECASE)
        new_content, n = pattern.subn(new, content)
        if n > 0:
            file_changes += n
            content = new_content

    # Tailwind replacements (exact string)
    for old, new in TAILWIND_REPLACEMENTS:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            file_changes += count

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[FIXED]  {filename} — {file_changes} replacement(s)")
        total_changes += file_changes
    else:
        print(f"[CLEAN]  {filename} — no changes needed")

print(f"\n✅ Done. Total replacements across all files: {total_changes}")
