"""patch_v26_pages.py – bulk-replace stale version strings across six files."""

import os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent  # …/is-chrp-v26-generative

# Each entry: (relative path, [(old, new), ...])
PATCHES = [
    ("legal.html", [
        ("Compliance Node v26.4", "Compliance Node v29.0"),
        ("v26.4", "v29.0"),
    ]),
    ("regulatory.html", [
        ("Regulatory Integrity v26.4", "Regulatory Integrity v29.0"),
        ("Version 26.4 | Build 0x771A GOLD", "Version 29.0 | Build 0x290_v29"),
        ("Zenith Ultra v26.4", "Zenith v29.0"),
        ("© 2026 Zenith v26.4 GOLD", "© 2026 Zenith v29.0"),
        ("v26.4", "v29.0"),
    ]),
    ("SCIENTIFIC_SUMMARY.md", [
        ("Zenith v26.1", "Zenith v29.0"),
    ]),
    ("SCIENTIFIC_ABSTRACT_V26.md", [
        ("0xZEN_v26.1_INST_MARCH_992B_COMP", "0xZEN_v29_INST_JUNE_1940K_COMP"),
        ("Zenith Ultra-v26.1", "Zenith v29.0"),
        ("Institutional v26.1", "v29.0"),
        ("Zenith v26.1", "Zenith v29.0"),
        ("v26.1", "v29.0"),
    ]),
    ("contact.html", [
        ("v28.0 GOLD", "v29.0"),
    ]),
    ("trials.html", [
        ("v28.0 GOLD", "v29.0"),
        ("500K-Cell Foundation GOLD Manifold", "2M-Cell Foundation Manifold"),
    ]),
]


def patch_file(rel: str, replacements: list[tuple[str, str]]) -> int:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    total = 0
    for old, new in replacements:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            total += count
    path.write_text(text, encoding="utf-8")
    return total


def main() -> None:
    grand = 0
    for rel, replacements in PATCHES:
        n = patch_file(rel, replacements)
        grand += n
        print(f"  {rel}: {n} replacement(s)")
    print(f"\nTotal: {grand} replacement(s) across {len(PATCHES)} files.")


if __name__ == "__main__":
    main()
