with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if 3330 <= idx <= 3735:
        if "manifold" in line:
            print(f"{idx}: {line.strip()}")
