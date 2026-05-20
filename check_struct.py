lines = open('index.html', encoding='utf-8', errors='replace').readlines()
ai_line = next((i for i,l in enumerate(lines,1) if 'AI ASSISTANT' in l and 'button' in l.lower()), None)
sim_start = next((i for i,l in enumerate(lines,1) if 'view-simulation' in l and 'div id' in l), None)
print('view-simulation starts at line:', sim_start)
print('AI ASSISTANT button at line:', ai_line)
if ai_line and sim_start:
    print('AI ASSISTANT is INSIDE simulation?', ai_line > sim_start)
