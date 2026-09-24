import sys, os
sys.stdout.reconfigure(encoding='utf-8')
with open('bridge_server.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for term in ['real-discovery/run', 'gpt-discovery/run', 'discover_hybrid']:
    idx = text.find(term)
    if idx != -1:
        print(f"=== LOCATION OF {term} (index {idx}) ===")
        print(text[idx-100:idx+1500])
        print("\n" + "="*50 + "\n")
