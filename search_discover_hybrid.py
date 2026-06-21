with open("js/script.js", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "discover_hybrid" in line:
        print(f"Line {idx}: {line.strip().encode('ascii', 'ignore').decode('ascii')}")
        for j in range(max(0, idx - 10), min(idx + 30, len(lines))):
            print(f"  {j+1}: {lines[j].strip().encode('ascii', 'ignore').decode('ascii')}")
