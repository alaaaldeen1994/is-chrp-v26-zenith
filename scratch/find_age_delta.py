import re

with open(r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find occurrences of 'Age Δ' or 'epigenetic' in JS code
pattern = r'(\w*age\w*|\w*delta\w*|epigenetic)'
matches = re.findall(r'(\d+\.\d+y|-[0-9\.]+y)', text)
print("Found age pattern matches:", set(matches))

# Search for the function that populates the discovery results HTML card
func_match = re.findall(r'function\s+(render\w+|handle\w+|run\w+)', text)
print("Found functions:", set(func_match))
