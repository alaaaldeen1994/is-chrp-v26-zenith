with open("js/script.js", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "biosimmode" in line.lower() and (":" in line or "=" in line):
            print(f"Line {idx}: {line.strip()}")
