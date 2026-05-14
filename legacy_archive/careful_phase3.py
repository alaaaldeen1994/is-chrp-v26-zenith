#!/usr/bin/env python3
"""
CAREFUL Phase 3 - FIXED: Find proper insertion points
"""

import subprocess
import re

def check_syntax():
    result = subprocess.run(['node', '--check', 'js/script.js'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

print("ðŸ–±ï¸ Phase 3: Cell Clicking (FIXED)...")
print("=" * 70)

with open('js/script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# PART 1: Add click handling initialization in init3D
# Find "this.dummy = new THREE.Object3D();" and add after it
for i, line in enumerate(lines):
    if 'this.dummy = new THREE.Object3D();' in line and i > 1300:
        print(f"Found dummy object at line {i+1}")
        insertion_point = i + 1
        
        click_init = [
            "\r\n",
            "            // PHASE 3: Cell Clicking System\r\n",
            "            this.raycaster = new THREE.Raycaster();\r\n",
            "            this.mouse = new THREE.Vector2();\r\n",
            "            this.selectedCellIndex = null;\r\n",
            "            \r\n",
            "            this.renderer.domElement.addEventListener('click', (event) => {\r\n",
            "                if (this.viewMode !== '3D') return;\r\n",
            "                const rect = this.renderer.domElement.getBoundingClientRect();\r\n",
            "                this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;\r\n",
            "                this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;\r\n",
            "                this.raycaster.setFromCamera(this.mouse, this.camera);\r\n",
            "                const intersects = this.raycaster.intersectObject(this.instancedMesh);\r\n",
            "                if (intersects.length > 0) {\r\n",
            "                    this.select3DCell(intersects[0].instanceId);\r\n",
            "                } else {\r\n",
            "                    this.deselect3DCell();\r\n",
            "                }\r\n",
            "            });\r\n",
        ]
        
        for j, code_line in enumerate(click_init):
            lines.insert(insertion_point + j, code_line)
        print(f"Inserted click initialization at line {insertion_point}")
        break

# PART 2: Add select/deselect methods after init3D closes
# Find closing brace of init3D
for i, line in enumerate(lines):
    if i > 1400 and line.strip() == '},':
        # Check if next line is another method or function
        if i + 1 < len(lines) and 'animate3D' in lines[i + 1]:
            print(f"Found init3D closing at line {i+1}")
            insertion_point = i + 1
            
            methods = [
                "\r\n",
                "        select3DCell(index) {\r\n",
                "            this.selectedCellIndex = index;\r\n",
                "            const agent = BiosimEngine.agents[index];\r\n",
                "            if (!agent) return;\r\n",
                "            const selInfo = document.getElementById('3d-selection-info');\r\n",
                "            if (selInfo) {\r\n",
                "                selInfo.classList.remove('hidden');\r\n",
                "                document.getElementById('sel-cell-id').textContent = agent.id || index;\r\n",
                "                document.getElementById('sel-cell-type').textContent = agent.type;\r\n",
                "                document.getElementById('sel-cell-age').textContent = ((agent.bioAge || 0) * 100).toFixed(1) + ' years';\r\n",
                "                document.getElementById('sel-cell-health').textContent = ((agent.health || 1) * 100).toFixed(0) + '%';\r\n",
                "            }\r\n",
                "        },\r\n",
                "\r\n",
                "        deselect3DCell() {\r\n",
                "            this.selectedCellIndex = null;\r\n",
                "            const selInfo = document.getElementById('3d-selection-info');\r\n",
                "            if (selInfo) selInfo.classList.add('hidden');\r\n",
                "        },\r\n",
            ]
            
            for j, code_line in enumerate(methods):
                lines.insert(insertion_point + j, code_line)
            print(f"Inserted select/deselect methods at line {insertion_point}")
            break

# PART 3: Add highlighting in animate3D
for i, line in enumerate(lines):
    if 'this.instancedMesh.setColorAt(i, color);' in line and i > 1400:
        print(f"Found setColorAt at line {i+1}")
        insertion_point = i + 1
        
        highlight = [
            "                // PHASE 3: Highlight selected\r\n",
            "                if (i === this.selectedCellIndex) {\r\n",
            "                    color.multiplyScalar(1.6);\r\n",
            "                    const hs = s * 1.25;\r\n",
            "                    this.dummy.scale.set(hs, hs, hs);\r\n",
            "                    this.dummy.updateMatrix();\r\n",
            "                    this.instancedMesh.setMatrixAt(i, this.dummy.matrix);\r\n",
            "                    this.instancedMesh.setColorAt(i, color);\r\n",
            "                }\r\n",
        ]
        
        for j, code_line in enumerate(highlight):
            lines.insert(insertion_point + j, code_line)
        print(f"Inserted highlighting at line {insertion_point}")
        break

# Write back
with open('js/script.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Test
print("\nTesting syntax...")
is_valid, error = check_syntax()

if is_valid:
    print("âœ… PHASE 3 COMPLETE!")
else:
    print("âŒ Error:")
    print(error)
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'js/script.js'])
