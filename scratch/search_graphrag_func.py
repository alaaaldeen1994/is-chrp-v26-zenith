import os

filepath = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\index.html"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        idx = content.find("grn-canvas-viewport")
        while idx != -1:
            print(f"Found grn-canvas-viewport at index {idx}")
            snippet = content[max(0, idx-100):min(len(content), idx+500)]
            print(snippet)
            print("--------------------------------------------------")
            idx = content.find("grn-canvas-viewport", idx+1)
