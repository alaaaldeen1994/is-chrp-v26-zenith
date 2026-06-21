"""
Patch profile.html: replace all v28 references with v29,
update cell counts (500K/486K -> 2M), and gene counts (4908 -> 5858).
"""
import re
from pathlib import Path

TARGET = Path(r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\profile.html")

content = TARGET.read_text(encoding="utf-8")
original = content  # keep a copy for diffing

# ── Ordered literal replacements (longest / most-specific first) ──────────
literal_replacements = [
    # Version strings – most specific first to avoid partial matches
    ("v28.0 GOLD GOLD", "v29.0"),
    ("v28.0 GOLD",      "v29.0"),
    ("v28.1",           "v29.0"),
    ("v28.0",           "v29.0"),

    # Cell counts
    ("500,000 baseline cells", "2,000,000 baseline cells"),
    ("500,000 cells",          "2,000,000 cells"),
    ("500K cells",             "2M cells"),
    ("486,134",                "2,000,000"),
    ("486k",                   "2M"),
    ("486K",                   "2M"),

    # Gene counts
    ("4,908 genes",            "5,858 genes"),
    ("4908 genes",             "5858 genes"),

    # Link text for clinical report
    ("Clinical Report v28.0 GOLD", "Clinical Report v29.0"),
    ("Clinical Report v28",        "Clinical Report v29"),

    # Filename references (href values)
    ("v28_clinical_report.html",   "v29_clinical_report.html"),
]

for old, new in literal_replacements:
    content = content.replace(old, new)

# ── Remaining bare "v28" -> "v29" ────────────────────────────────────────
# We need to be careful not to break HTML id/class tokens that happen to
# contain "v28".  Strategy: replace only occurrences that are NOT immediately
# preceded by a hyphen or underscore AND not inside an HTML attribute value
# that looks like an id/class token (e.g. id="something-v28").
#
# A simple safe heuristic: replace "v28" only when it is preceded by a
# word-boundary-like character (space, quote, >, (, start-of-line) and
# followed by a word-boundary-like character (space, quote, <, ), comma,
# period, end-of-line, or a digit like in "v28.0" which was already handled).
# But since the specific v28.0/v28.1 patterns are already handled above,
# the remaining "v28" occurrences are bare version labels.
#
# Let's just do a plain replace – the specific patterns above already
# consumed the important ones, and any remaining "v28" should also become "v29".
content = content.replace("v28", "v29")

# ── Gene dimension number (standalone 4908) ──────────────────────────────
# Replace "4908" when it appears in gene-dimension contexts.
# Use regex to replace 4908 that is surrounded by non-digit characters
# (to avoid replacing inside larger numbers).
content = re.sub(r'(?<!\d)4908(?!\d)', '5858', content)

# ── Also handle "500,000" that wasn't followed by " cells" or " baseline" ─
# (e.g. "500,000" standalone references)
content = content.replace("500,000", "2,000,000")

# ── Also handle standalone "500K" not followed by " cells" ───────────────
content = content.replace("500K", "2M")

# ── Write back ───────────────────────────────────────────────────────────
TARGET.write_text(content, encoding="utf-8")

# ── Report ───────────────────────────────────────────────────────────────
n_changed = sum(1 for a, b in zip(original.splitlines(), content.splitlines()) if a != b)
print(f"Done. {n_changed} lines changed.")

# Show remaining v28 occurrences (should be zero)
remaining = [
    (i + 1, line)
    for i, line in enumerate(content.splitlines())
    if "v28" in line.lower()
]
if remaining:
    print(f"WARNING: {len(remaining)} lines still contain 'v28':")
    for num, line in remaining:
        print(f"  L{num}: {line.strip()[:120]}")
else:
    print("Verified: no remaining 'v28' references.")
