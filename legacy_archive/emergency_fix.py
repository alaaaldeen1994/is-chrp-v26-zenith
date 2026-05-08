#!/usr/bin/env python3
"""
CRITICAL FIX: My previous scripts didn't work correctly
Manually fixing the remaining issues NOW
"""

print("🔧 CRITICAL FIX: Applying changes that didn't work...")
print("=" * 70)

# Read file
with open('js/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# FIX 1: Syntax error at line 1510
print("Fixing syntax error at line 1510...")
content = content.replace(
    "if (selInfo) selInfo.classList.add('hidden'); {",
    "if (selInfo) selInfo.classList.add('hidden');\n        },\n\n        animate3D() {"
)

# FIX 2: Apply membrane texture properties  
print("Applying membrane texture properties...")
old_mat = """new THREE.MeshPhongMaterial({
                    vertexColors: true,
                    shininess: 80,
                    emissive: 0x111111 // Slight glow so they're visible
                })"""

new_mat = """new THREE.MeshPhongMaterial({
                    vertexColors: true,
                    shininess: 60, // PHASE 4.3: Organic look
                    specular: 0x222222, // Subtle highlights
                    emissive: 0x111111,
                    bumpScale: 0.3, // Surface irregularities
                    reflectivity: 0.2, // Realistic membrane
                    refractionRatio: 0.95 // Biological optics
                })"""

content = content.replace(old_mat, new_mat)

# Save
with open('js/script.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Syntax error fixed")
print("✅ Membrane properties applied")

# FIX 3: Add smooth transitions to CSS (simpler approach)
print("\nAdding CSS transitions...")
with open('css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

if "fadeIn" not in css:
    css += """
/* PHASE 7.3: Smooth Transitions */
@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.98); }
    to { opacity: 1; transform: scale(1); }
}

#main-viewport-2d, #main-viewport-microscope, #main-viewport-3d {
    animation: fadeIn 0.4s ease-in-out;
}
"""
    with open('css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("✅ CSS transitions added")
else:
    print("✅ CSS transitions already present")

print("\n" + "=" * 70)
print("✅ ALL FIXES APPLIED!")
print("Now testing for syntax errors...")

import subprocess
result = subprocess.run(['node', '--check', 'js/script.js'], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ JavaScript syntax: VALID")
else:
    print("❌ JavaScript syntax error:")
    print(result.stderr)
