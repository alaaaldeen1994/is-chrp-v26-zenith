lines = open('index.html', encoding='utf-8', errors='replace').readlines()
for i, l in enumerate(lines, 1):
    if any(x in l for x in ['view-discovery', 'view-simulation', 'enterSimulation', 'exitSimulation', 'END #view']):
        print(i, l.rstrip()[:110])
