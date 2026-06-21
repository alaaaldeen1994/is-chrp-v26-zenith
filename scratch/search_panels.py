import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\index.html"
lines_to_print = [
    (5035, 5055),
    (5370, 5385),
    (5510, 5525)
]

if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for start, end in lines_to_print:
            print(f"\n--- Lines {start} to {end} ---")
            for idx in range(start-1, min(end, len(lines))):
                print(f"Line {idx+1}: {lines[idx].strip()}")
