
import os

source = 'index.html'
dest = 'index_refactored.html'

with open(source, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(dest, 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        line_num = i + 1 # 1-based
        
        # CSS Block: 22 to 499
        if 22 <= line_num <= 499:
            if line_num == 22:
                f.write('    <link rel="stylesheet" href="css/style.css">\n')
            continue
            
        # Main JS Block: 1141 to 3816
        if 1141 <= line_num <= 3816:
            if line_num == 1141:
                f.write('    <script src="js/script.js"></script>\n')
            continue
            
        # VisionBridge JS Block: 3874 to 3983
        if 3874 <= line_num <= 3983:
            continue
            
        f.write(line)

print("Refactoring complete.")
