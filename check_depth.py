
def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    depth = 0
    line = 1
    for i, char in enumerate(content):
        if char == '\n':
            line += 1
        
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        
        if line == 1059:
            print(f"Stack depth at line 1059: {depth}")
            break

check_braces(r'c:\Users\tariq\.gemini\antigravity\scratch\is-chrp-v26-generative\js\script.js')
