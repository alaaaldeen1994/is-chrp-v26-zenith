with open("index.html", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "5000" in line or "5,000" in line:
            print(f"Line {idx}: {line.strip()}")
