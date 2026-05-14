
def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    line = 1
    col = 1
    for i, char in enumerate(content):
        if char == '\n':
            line += 1
            col = 1
        else:
            col += 1
        
        if char == '{':
            stack.append(('{', line, col))
        elif char == '}':
            if not stack:
                print(f"Extra closing brace at line {line}, col {col}")
                return
            stack.pop()
    
    if stack:
        for char, l, c in stack:
            print(f"Unclosed brace {char} from line {l}, col {c}")
    else:
        print("Braces are balanced")

check_braces(r'c:\Users\tariq\.gemini\antigravity\scratch\is-chrp-v26-generative\js\script.js')
