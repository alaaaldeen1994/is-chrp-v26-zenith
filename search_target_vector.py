with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "def get_target_vector_from_query" in line:
        print(f"Line {idx}: {line.strip()}")
        for j in range(idx, min(idx + 60, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
