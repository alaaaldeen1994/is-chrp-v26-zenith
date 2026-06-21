"""
Patch secondary HTML pages and markdown files:
  - v28 → v29
  - 500K / 500,000 / 486,134 cell counts → 2,000,000 / 2M
  - 4,908 genes → 5,858 genes
  - 14 donors → 83 donors  (training-data context)
  - 2 batches → 11 datasets (training-data context)
"""

import os, re

BASE = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"

FILES = [
    "about.html",
    "evidence.html",
    "how_it_works.html",
    "whitepaper.html",
    "scientific_qna.html",
    "ZENITH_FOUNDATION_MODEL_CARD.md",
    "SCIENTIFIC_SUMMARY.md",
    "README.md",
]

# Ordered list of (pattern, replacement) — order matters (longer/more-specific first)
REPLACEMENTS = [
    # Version strings (most specific first)
    ("v28.0 GOLD", "v29.0"),
    ("v28.0", "v29.0"),
    ("v28", "v29"),

    # Cell counts — exact numbers
    ("2,000,000", "2,000,000"),        # already correct → no-op guard
    ("500,000 cells", "2,000,000 cells"),
    ("500,000", "2,000,000"),
    ("486,134", "2,000,000"),

    # Cell counts — abbreviated
    ("500K cells", "2M cells"),
    ("500K", "2M"),
    ("500k cells", "2M cells"),
    ("500k", "2M"),
    ("486K", "2M"),
    ("486k", "2M"),

    # Gene count
    ("4,908 genes", "5,858 genes"),
    ("4908 genes", "5,858 genes"),

    # Donor / batch counts (training-data context)
    ("14 donors", "83 donors"),
    ("2 batches", "11 datasets"),
]


def patch_file(path: str) -> list[str]:
    """Apply all replacements to *path*. Return list of change descriptions."""
    with open(path, encoding="utf-8") as f:
        original = f.read()

    text = original
    changes: list[str] = []

    for old, new in REPLACEMENTS:
        if old == new:
            continue  # skip no-op guards
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            changes.append(f"  '{old}' -> '{new}'  ({count} occurrence(s))")

    if text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    return changes


def main():
    total_files_changed = 0
    for fname in FILES:
        fpath = os.path.join(BASE, fname)
        if not os.path.isfile(fpath):
            print(f"!! SKIPPED (not found): {fname}")
            continue

        changes = patch_file(fpath)
        if changes:
            total_files_changed += 1
            print(f"OK {fname}")
            for c in changes:
                print(c)
        else:
            print(f"-- {fname}  (no matches)")

    print(f"\nDone. {total_files_changed}/{len(FILES)} file(s) modified.")


if __name__ == "__main__":
    main()
