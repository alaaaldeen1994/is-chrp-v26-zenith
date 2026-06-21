with open("js/script.js", "r", encoding="utf-8", errors="ignore") as f:
    for idx, line in enumerate(f, 1):
        if "const BiosimBridge" in line or "var BiosimBridge" in line or "let BiosimBridge" in line or "BiosimBridge =" in line:
            print(f"Line {idx}: {line.strip()}")
