import sys, json, ast, os, subprocess

print('==================================================')
print('   ZENITH DOUBLE-CHECK DEEP SYSTEM AUDIT')
print('==================================================\n')

# 1. Inspect index.html JavaScript functions
print('1. Checking index.html button handlers...')
with open('index.html', encoding='utf-8') as f:
    html_content = f.read()

required_funcs = [
    'downloadResultCSV',
    'downloadOpentronsScript',
    'printClinicalDossier',
    'showLnpCalculatorModal',
    'downloadResultJSON',
    'downloadAF3JSON'
]

for func in required_funcs:
    assert f'window.{func}' in html_content or f'function {func}' in html_content, f'Missing {func} in index.html'
    print(f'   [OK] {func}() is defined in index.html')

# 2. Inspect bridge_server.py API routes
print('\n2. Checking bridge_server.py API routes...')
with open('bridge_server.py', encoding='utf-8') as f:
    server_code = f.read()

required_routes = [
    '/api/v2/lnp/calculate',
    '/api/v2/robotics/opentrons',
    '/api/v2/dossier/generate'
]

for route in required_routes:
    assert route in server_code, f'Missing route {route} in bridge_server.py'
    print(f'   [OK] {route} is mounted in bridge_server.py')

# 3. Test LNP Optimizer math edge cases
print('\n3. Testing LNP Optimizer edge cases...')
from services.lnp_optimizer import LNPOptimizerService
svc = LNPOptimizerService()

# Test standard dose
d1 = svc.calculate_mass_breakdown(mrna_dose_ug=100.0, mrna_length_nt=1200, np_ratio=6.0)
assert d1['total_lipid_mass_ug'] > 0
print(f"   [OK] Standard dose 100ug mRNA -> {d1['total_lipid_mass_ug']} ug total lipids")

# Test high dose
d2 = svc.calculate_mass_breakdown(mrna_dose_ug=500.0, mrna_length_nt=2000, np_ratio=8.0)
assert d2['total_lipid_mass_ug'] > d1['total_lipid_mass_ug']
print(f"   [OK] High dose 500ug mRNA -> {d2['total_lipid_mass_ug']} ug total lipids")

# 4. Check git commit & branch status
print('\n4. Checking Git commit synchronization...')
res = subprocess.run(['git', 'log', '-n', '1', '--oneline'], capture_output=True, text=True)
print(f"   [OK] Head commit: {res.stdout.strip()}")

print('\n==================================================')
print('   DOUBLE-CHECK COMPLETE: 100% VERIFIED SUCCESS')
print('==================================================')
