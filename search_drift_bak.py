with open("bridge_server.py.bak", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "drift" in line:
            if "drift =" in line or "drift=" in line:
                print(f"Line {idx}: {line.strip()}")
