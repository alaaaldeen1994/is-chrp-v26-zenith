import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
cwd = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
with open(os.path.join(cwd, 'bridge_server.py'), 'r', encoding='utf-8', errors='ignore') as f:
    server = f.read()

route_pattern = re.compile(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']')
routes = route_pattern.findall(server)
keywords = ['discover', 'partial', 'simulate', 'manifold', 'query', 'search', 'trial', 'longevity', 'longev', 'age', 'reprog', 'biomarker', 'ensemble']
disc_routes = [(m, r) for m, r in routes if any(k in r.lower() for k in keywords)]
print('=== DISCOVERY / REPROGRAMMING / LONGEVITY ROUTES ===')
for m, r in disc_routes:
    print(f'  [{m.upper()}] {r}')

# Also check DiscoveryRequest schema
disc_idx = server.find('class DiscoveryRequest')
if disc_idx >= 0:
    print('\n=== DiscoveryRequest Schema ===')
    print(server[disc_idx:disc_idx+600])
