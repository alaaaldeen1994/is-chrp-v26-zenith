with open('bridge_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'real-discovery' in line or 'gpt-discovery' in line or 'discover_hybrid' in line:
        print(f"Line {i+1}: {line.strip()}")
