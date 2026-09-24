import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
path = os.path.join(base, 'profile.html')

with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

lines = content.split('\n')
print(f"Total lines in profile.html: {len(lines)}")

# Find all section tags
sections = []
for i, line in enumerate(lines):
    if '<section' in line:
        sections.append((i+1, line.strip()))

print(f"Found {len(sections)} section tags:")
for line_num, tag in sections:
    print(f"Line {line_num}: {tag[:100]}")

# Also check for .reveal in embedded CSS or JS
reveal_matches = []
for i, line in enumerate(lines):
    if 'reveal' in line:
        reveal_matches.append((i+1, line.strip()))

print(f"\nFound {len(reveal_matches)} lines containing 'reveal':")
for line_num, line_str in reveal_matches:
    print(f"Line {line_num}: {line_str[:120]}")
