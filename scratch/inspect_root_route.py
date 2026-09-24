with open('bridge_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[:120]):
    if '@app.get("/")' in line or '@app.get(\'/\')' in line:
        print(f"Root route defined at line {i+1}:")
        for j in range(25):
            if i+j < len(lines):
                print(f"  {lines[i+j]}", end='')
        break
else:
    for i, line in enumerate(lines):
        if 'def get_root' in line or 'def read_root' in line or 'def serve_root' in line or '@app.get("/")' in line:
            print(f"Found root route at line {i+1}:")
            for j in range(25):
                if i+j < len(lines):
                    print(f"  {lines[i+j]}", end='')
            break
