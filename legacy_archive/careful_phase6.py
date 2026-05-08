#!/usr/bin/env python3
"""
Phase 6: Complete View Isolation
"""

print("🔒 Phase 6: View Isolation...")
print("=" * 70)

with open('css/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Add comprehensive isolation rules
if "PHASE 6: COMPLETE VIEW ISOLATION" not in css:
    isolation_css = """
/* ========================================
   PHASE 6: COMPLETE VIEW ISOLATION
   ======================================== */

/* Hide 3D status panel in other views */
#main-viewport-2d #3d-status-panel,
#main-viewport-microscope #3d-status-panel {
    display: none !important;
}

/* Hide HUD panel in 3D */
#main-viewport-3d .hud-panel {
    display: none !important;
}

/* Hide legends in wrong views */
#main-viewport-3d .KAGAWEA-legend,
#main-viewport-microscope .KAGAWEA-legend {
    display: none !important;
}

/* Ensure selection info only in 3D */
#main-viewport-2d #3d-selection-info,
#main-viewport-microscope #3d-selection-info {
    display: none !important;
}
"""
    
    css += isolation_css
    
    with open('css/style.css', 'w', encoding='utf-8') as f:
        f.write(css)
    
    print("✅ View isolation CSS rules added")
    print("   - 3D panel hidden in 2D/Microscopy")
    print("   - HUD hidden in 3D")
    print("   - Legends properly scoped")
    print("   - Selection info only in 3D")
else:
    print("✅ View isolation already present")

print("\n✅ PHASE 6 COMPLETE!")
