import re

with open(r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\technical_catalog.html', 'r', encoding='utf-8') as f:
    content = f.read()

headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', content, re.DOTALL)
print(f"Total headings found: {len(headings)}")
for i, h in enumerate(headings[:30]):
    clean = re.sub(r'<[^>]+>', '', h).strip()
    print(f"{i+1}. {clean}")
