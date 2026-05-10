import os

def fix_file(filename, replacements):
    if not os.path.exists(filename):
        return
    with open(filename, 'rb') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filename, 'wb') as f:
        f.write(content)
    print(f"Binary fix applied to {filename}")

# replacements as (binary_old, binary_new)
reps = [
    (b"\xc3\x83\xc6\x92\xc3\x82\xc2\xa3\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xb0\xc3\x83\xc6\x92\xc3\x82\xc2\xa5\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xb8\xc3\x83\xe2\x80\x9a\xc3\x82\xe2\x80\x93\xc3\x83\xc6\x92\xc3\x82\xc2\xa3\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xa8\xc3\x83\xc6\x92\xc3\x82\xc2\xa6\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xaf\xc3\x83\xc6\x92\xc3\x82\xc2\xa5\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\xb8\xc3\x83\xc6\x92\xc3\x82\xc2\xa5\xc3\x83\xe2\x80\x9a\xc3\x82\xc2\x8f", b"&#128424;"),
    # Let's use simpler substrings if the above is too brittle
    (b"\xc3\x82\xc2\xb1", b"&plusmn;"), # Â±
    (b"\xc3\x82\xc2\xb5", b"&micro;"), # Âµ
    (b"\xc3\x82\xc2\xa9", b"&copy;"),  # Â©
    (b"\xc3\x82\xc2\xb7", b"&middot;"), # Â·
    (b"\xc3\x83\xc2\xa2\xc3\xa2\x82\xac\xc3\xa2\xe2\x82\xac\x9d", b"&mdash;"), # â€”
    (b"\xc3\xa2\xe2\x82\xac\xe2\x80\x9d", b"&mdash;"),
    (b"\xc3\xa2\xe2\x80\x9d\xc5\x92", b"&mdash;"),
    (b"â€”", b"&mdash;"),
    (b"â†’", b"&rarr;"),
    (b"â€¦", b"..."),
]

# Specifically for the print button which is the most mangled
with open('index.html', 'rb') as f:
    content = f.read()
    # Search for the anchor "PRINT CLINICAL REPORT" and replace the prefix
    marker = b" PRINT CLINICAL REPORT"
    pos = content.find(marker)
    if pos != -1:
        # Go back 30 bytes and find the start of the button content
        start = pos - 30
        end = pos
        # Replace the garbage between the last > and the marker
        fragment = content[start:end]
        last_bracket = fragment.rfind(b">")
        if last_bracket != -1:
            garbage = fragment[last_bracket+1:]
            content = content.replace(garbage + marker, b"&#128424;" + marker)

with open('index.html', 'wb') as f:
    f.write(content)

fix_file('profile.html', reps)
fix_file('technical_catalog.html', reps)
