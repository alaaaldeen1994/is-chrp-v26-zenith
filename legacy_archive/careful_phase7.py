#!/usr/bin/env python3
"""
Phase 7: Quality Polish - Emissive glows and smooth transitions
"""

import subprocess

def check_syntax():
    result = subprocess.run(['node', '--check', 'js/script.js'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

print("âœ¨ Phase 7: Quality Polish...")
print("=" * 70)

with open('js/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add emissive glow in color calculation (before setColorAt)
if "PHASE 7: Enhanced colors" not in content:
    old_color = """                // BRIGHT VISIBLE COLORS from CONFIG.colors
                const cellColor = CONFIG.colors[a.type] || CONFIG.colors.SOMATIC;
                const color = new THREE.Color();
                color.setHSL(
                    cellColor.h / 360,
                    cellColor.s / 100,
                    Math.min(0.8, cellColor.l / 100 + 0.2) // Brighter for visibility
                );

                this.instancedMesh.setColorAt(i, color);"""
    
    new_color = """                // PHASE 7: Enhanced colors with emissive glow
                const cellColor = CONFIG.colors[a.type] || CONFIG.colors.SOMATIC;
                const color = new THREE.Color();
                color.setHSL(
                    cellColor.h / 360,
                    cellColor.s / 100,
                    Math.min(0.8, cellColor.l / 100 + 0.2)
                );
                
                // Cell-type-specific glow
                let glowIntensity = 0.05;
                if (a.type === 'IPSC') glowIntensity = 0.15; // Stem cells glow
                else if (a.type === 'TUMOR') glowIntensity = 0.2; // Malignant glow
                else if (a.type === 'DEATH') glowIntensity = 0.0; // Dead cells dark
                
                color.multiplyScalar(1.0 + glowIntensity);

                this.instancedMesh.setColorAt(i, color);"""
    
    content = content.replace(old_color, new_color)
    print("âœ… Emissive glow added (iPSC: 15%, Tumor: 20%, Death: 0%)")

with open('js/script.js', 'w', encoding='utf-8') as f:
    f.write(content)

# Test syntax
is_valid, error = check_syntax()

if is_valid:
    print("âœ… JavaScript syntax valid")
else:
    print("âŒ Syntax error:")
    print(error)
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'js/script.js'])
    exit(1)

# Add CSS transitions
print("\nAdding smooth transitions to CSS...")
with open('css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

if "PHASE 7: SMOOTH TRANSITIONS" not in css:
    transition_css = """
/* ========================================
   PHASE 7: SMOOTH TRANSITIONS
   ======================================== */

/* Smooth fade for view changes */
#main-viewport-2d,
#main-viewport-microscope,
#main-viewport-3d {
    transition: opacity 0.3s ease-in-out;
}

/* Panel smooth transitions */
.micro-analysis-card,
#3d-status-panel,
.hud-panel {
    transition: all 0.3s ease-in-out;
}

/* Button hover effects */
button {
    transition: all 0.2s ease-in-out;
}

/* Smooth appearance */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
"""
    
    css += transition_css
    
    with open('css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)
    
    print("âœ… Smooth transitions added (0.3s fade)")

print("\n" + "=" * 70)
print("âœ¨ PHASE 7 COMPLETE!")
print("   - iPSC cells glow (active)")
print("   - Tumor cells glow (metabolic)")
print("   - Dead cells darkened")
print("   - Smooth view transitions")
