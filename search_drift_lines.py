with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if 3300 <= idx <= 3450:
            if "drift" in line:
                print(f"Line {idx}: {line.strip()}")
