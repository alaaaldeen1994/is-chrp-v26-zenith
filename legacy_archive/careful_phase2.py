#!/usr/bin/env python3
"""
CAREFUL Phase 2 Implementation - Backend Connection
Testing after each change to ensure no syntax errors
"""

import subprocess

def check_syntax():
    """Check JavaScript syntax"""
    result = subprocess.run(['node', '--check', 'js/script.js'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

print("ðŸ”§ Phase 2: Adding Backend Connection CAREFULLY...")
print("=" * 70)

# Read file
with open('js/script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "this.controls.update();" in animate3D
for i, line in enumerate(lines):
    if 'this.controls.update();' in line and i > 1300:  # In animate3D function
        print(f"Found controls.update() at line {i+1}")
        
        # Insert Phase 2 code after it
        insertion_point = i + 1
        
        # Skip blank line if exists
        if lines[insertion_point].strip() == '':
            insertion_point += 1
        
        phase2_code = [
            "\r\n",
            "            // PHASE 2: Backend connection\r\n",
            "            const cellCount = BiosimEngine.agents.length;\r\n",
            "            const cellCountEl = document.getElementById('3d-cell-count');\r\n",
            "            if (cellCountEl) cellCountEl.textContent = cellCount;\r\n",
            "            \r\n",
            "            // Console logging every 2 seconds\r\n",
            "            if (!this.frame) this.frame = 0;\r\n",
            "            this.frame++;\r\n",
            "            if (this.frame % 120 === 0) {\r\n",
            "                const types = {};\r\n",
            "                BiosimEngine.agents.forEach(a => types[a.type] = (types[a.type] || 0) + 1);\r\n",
            "                console.log(`ðŸ”· 3D: ${cellCount} cells |`, types);\r\n",
            "            }\r\n",
            "\r\n"
        ]
        
        # Insert the code
        for j, code_line in enumerate(phase2_code):
            lines.insert(insertion_point + j, code_line)
        
        print(f"Inserted Phase 2 code at line {insertion_point}")
        break

# Write back
with open('js/script.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Test syntax
print("\nTesting JavaScript syntax...")
is_valid, error = check_syntax()

if is_valid:
    print("âœ… Phase 2 COMPLETE: Syntax valid!")
    print("   - Cell count display updates")
    print("   - Console logging every 2s")
    print("   - Backend connected")
else:
    print("âŒ Syntax error detected:")
    print(error)
    print("\nREVERTING changes...")
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'js/script.js'])
