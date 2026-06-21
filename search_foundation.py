with open("bridge_server.py", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "zenith_foundation_v1" in line:
            print(f"Line {idx}: {line.strip()}")
