import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
services_dir = os.path.join(cwd, 'services')

print('=== BIOMARKER & REPROGRAMMING SERVICES ===')
for f in sorted(os.listdir(services_dir)):
    if not f.endswith('.py'):
        continue
    fpath = os.path.join(services_dir, f)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
        code = fh.read()
    keywords = ['biomarker', 'reprogramm', 'yamanaka', 'oct4', 'sox2', 'klf4', 'myc', 'cardiac', 'rejuvenat', 'partial']
    found = [k for k in keywords if k.lower() in code.lower()]
    if found:
        print(f'  {f}: {found}')

print()
with open(os.path.join(cwd, 'bridge_server.py'), 'r', encoding='utf-8', errors='ignore') as f:
    server = f.read()

route_pattern = re.compile(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']')
routes = route_pattern.findall(server)
bio_keywords = ['biomarker', 'reprogramm', 'yamanaka', 'partial', 'factor', 'cardiac', 'chrp', 'rejuvenat']
bio_routes = [(m, r) for m, r in routes if any(k in r.lower() for k in bio_keywords)]

print('=== BIOMARKER & REPROGRAMMING API ROUTES IN BRIDGE_SERVER ===')
for method, route in bio_routes:
    print(f'  [{method.upper()}] {route}')

# Also scan partial_safety.py which is a large relevant file
partial_path = os.path.join(cwd, 'partial_safety.py')
if os.path.exists(partial_path):
    with open(partial_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    classes = re.findall(r'class\s+(\w+)', code)
    functions = re.findall(r'def\s+(\w+)', code)
    print(f'\npartial_safety.py -> Classes: {classes[:8]}')
    print(f'partial_safety.py -> Key Functions: {functions[:10]}')
