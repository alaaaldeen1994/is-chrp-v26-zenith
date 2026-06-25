import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"
server_path = os.path.join(base_dir, "bridge_server.py")

with open(server_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching bridge_server.py for 1.94M, Generalist, and Ensemble ---")
search_terms = ["1.94M", "1,940,000", "Generalist", "Ensemble", "2,426,000", "2426000"]
for term in search_terms:
    print(f"\nSearching for: {term}")
    found = False
    for idx, line in enumerate(lines):
        if term in line:
            found = True
            print(f"L{idx+1}: {line.strip()}")
            # Print context
            start = max(0, idx - 3)
            end = min(len(lines), idx + 4)
            for c_idx in range(start, end):
                prefix = "-> " if c_idx == idx else "   "
                print(f"{prefix}L{c_idx+1}: {lines[c_idx].rstrip()}")
            print("----------------")
    if not found:
        print("Not found in bridge_server.py")
