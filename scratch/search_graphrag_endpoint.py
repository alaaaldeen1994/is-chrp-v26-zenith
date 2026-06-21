import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative\bridge_server.py"
if os.path.exists(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
        # Search for the graphrag route
        idx = content.find("/api/v1/clinical/graphrag/query")
        if idx != -1:
            print(f"Found GraphRAG endpoint at char index {idx}")
            snippet = content[max(0, idx-100):min(len(content), idx+4000)]
            print(snippet)
else:
    print("bridge_server.py not found")
