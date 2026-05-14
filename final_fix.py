import os

def final_fix():
    path = 'bridge_server.py'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # Fix the dangling backslash line
        if 'result["protein_name"] = rec.get("fullName", {}).get("value") or \\' in line:
            # Change to use parentheses for safe continuation
            new_lines.append('            result["protein_name"] = (rec.get("fullName", {}).get("value") or \n')
        elif 'names.get("submissionNames", [{}])[0].get("fullName", {}).get("value")' in line and len(new_lines) > 0 and 'result["protein_name"] =' in new_lines[-1]:
             new_lines.append(line.rstrip() + ')\n')
        else:
            new_lines.append(line)
            
    sanitized = "".join(c if ord(c) < 128 else " " for c in "".join(new_lines))
    
    with open(path, 'w', encoding='ascii', newline='\n') as f:
        f.write(sanitized)
    print("Fixed bridge_server.py with parentheses")

if __name__ == "__main__":
    final_fix()
