#!/usr/bin/env python3
"""
Phase 4: Biological Cell Morphology  
Cell-type-specific scaling/rotation
"""

import subprocess

def check_syntax():
    result = subprocess.run(['node', '--check', 'js/script.js'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

print("🔬 Phase 4: Biological Morphology...")
print("=" * 70)

with open('js/script.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the scale section in animate3D
for i, line in enumerate(lines):
    if '// Scale based on health' in line and i > 1400:
        print(f"Found scale section at line {i+1}")
        
        # Find the lines to replace (should be 2-3 lines)
        start_line = i
        end_line = i + 3  # "const s = ..."; "this.dummy.scale.set..."
        
        # New morphology code
        new_code = [
            "                // PHASE 4: Biological morphology\r\n",
            "                let scaleX = 1.0, scaleY = 1.0, scaleZ = 1.0;\r\n",
            "                const baseScale = 1.0 + (a.health || 1.0) * 0.3;\r\n",
            "                const ageScale = 1.0 - (a.bioAge || 0.5) * 0.2;\r\n",
            "                \r\n",
            "                switch(a.type) {\r\n",
            "                    case 'SOMATIC':\r\n",
            "                        scaleX = baseScale * 0.8;\r\n",
            "                        scaleY = baseScale * 2.0 * ageScale;\r\n",
            "                        scaleZ = baseScale * 0.8;\r\n",
            "                        this.dummy.rotation.z = (i % 360) * Math.PI / 180;\r\n",
            "                        break;\r\n",
            "                    case 'IPSC':\r\n",
            "                        const wobble = 0.9 + Math.sin(i * 0.5) * 0.1;\r\n",
            "                        scaleX = baseScale * 1.2 * wobble;\r\n",
            "                        scaleY = baseScale * 1.2;\r\n",
            "                        scaleZ = baseScale * 1.2 * wobble;\r\n",
            "                        break;\r\n",
            "                    case 'CARDIO':\r\n",
            "                        scaleX = baseScale * 0.7;\r\n",
            "                        scaleY = baseScale * 2.5 * ageScale;\r\n",
            "                        scaleZ = baseScale * 0.7;\r\n",
            "                        this.dummy.rotation.x = Math.PI / 2;\r\n",
            "                        break;\r\n",
            "                    case 'NEURO':\r\n",
            "                        scaleX = scaleY = scaleZ = baseScale * 0.6;\r\n",
            "                        break;\r\n",
            "                    case 'TUMOR':\r\n",
            "                        const irreg = 0.8 + Math.random() * 0.4;\r\n",
            "                        scaleX = baseScale * 1.3 * irreg;\r\n",
            "                        scaleY = baseScale * 1.3;\r\n",
            "                        scaleZ = baseScale * 1.3 * irreg;\r\n",
            "                        break;\r\n",
            "                    case 'DEATH':\r\n",
            "                        scaleX = scaleY = scaleZ = baseScale * 0.4;\r\n",
            "                        break;\r\n",
            "                    default:\r\n",
            "                        scaleX = scaleY = scaleZ = baseScale * ageScale;\r\n",
            "                }\r\n",
            "                \r\n",
            "                this.dummy.scale.set(scaleX, scaleY, scaleZ);\r\n",
        ]
        
        # Remove old lines and insert new
        del lines[start_line:end_line]
        for j, code_line in enumerate(new_code):
            lines.insert(start_line + j, code_line)
        
        print("✅ Inserted biological morphology code")
        break

with open('js/script.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

is_valid, error = check_syntax()

if is_valid:
    print("✅ PHASE 4 COMPLETE!")
    print("   - SOMATIC: 2:1 elongated")
    print("   - iPSC: Rounded with wobble")
    print("   - CARDIO: 2.5:1 rod")
    print("   - NEURO: 0.6x small")
    print("   - TUMOR: Irregular 1.3x")
    print("   - DEATH: 0.4x shrunken")
else:
    print("❌ Error:")
    print(error)
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'js/script.js'])
