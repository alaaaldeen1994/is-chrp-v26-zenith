"""Fix double-encoded UTF-8 in technical_catalog.html"""
import os

filepath = os.path.join(os.path.dirname(__file__), "technical_catalog.html")

with open(filepath, "rb") as f:
    raw = f.read()

# The file has double-encoded UTF-8 sequences
# Fix: decode as UTF-8, then replace known double-encoded patterns
text = raw.decode("utf-8")

# Replace double-encoded author name with clean ASCII-safe version
# The bytes c385 cb86 = double-encoded Åˆ, c383 c2a1 = double-encoded Ã¡
replacements = {
    "Litvi\u00c5\u02c6ukov\u00c3\u00a1": "Litvinukova",  # ASCII-safe
    "\u00e2\u20ac\u201c": "\u2014",  # em-dash
    "\u00e2\u20ac\u2122": "'",       # right single quote
    "\u00e2\u20ac\u0153": '"',       # left double quote
    "\u00c3\u2014": "\u00d7",        # multiplication sign
}

count_total = 0
for old, new in replacements.items():
    if old in text:
        c = text.count(old)
        text = text.replace(old, new)
        count_total += c
        print(f"Replaced {c}x: {repr(old[:20])} -> {repr(new)}")

# Also do a scan for the raw problematic sequences and replace
# Author name pattern: find all occurrences
import re
# Pattern for the double-encoded author name
author_pattern = text.count("Litvi")
print(f"Found {author_pattern} 'Litvi' occurrences")

# Check remaining encoding issues
remaining_issues = 0
for char in text:
    if ord(char) > 127 and ord(char) < 256:
        # Characters in Latin-1 extended range that shouldn't be there
        if char in '\u00c3\u00c5\u00c2\u00cb':
            remaining_issues += 1

print(f"Remaining suspicious high-byte chars: {remaining_issues}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Total replacements: {count_total}")
print("File saved as clean UTF-8.")
