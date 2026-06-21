with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if 4700 <= idx <= 4750:
        print(f"{idx}: {line.strip()}")
