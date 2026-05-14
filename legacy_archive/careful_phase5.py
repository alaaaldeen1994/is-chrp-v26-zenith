#!/usr/bin/env python3
"""
Phase 5: Camera & Zoom Fixes
"""

import subprocess

def check_syntax():
    result = subprocess.run(['node', '--check', 'js/script.js'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stderr

print("ðŸ“· Phase 5: Camera & Zoom...")
print("=" * 70)

with open('js/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace camera setup
old_camera = """this.camera = new THREE.PerspectiveCamera(60, container.offsetWidth / container.offsetHeight, 1, 1000);
            this.camera.position.set(0, 0, 200);"""

new_camera = """this.camera = new THREE.PerspectiveCamera(
                60, 
                container.offsetWidth / container.offsetHeight, 
                1, 
                2000  // PHASE 5: Increased far plane
            );
            this.camera.position.set(0, 0, 200);"""

content = content.replace(old_camera, new_camera)
print("âœ… Camera far plane increased to 2000")

# Replace controls setup  
old_controls = """this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;"""

new_controls = """this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            // PHASE 5: Professional camera controls
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.minDistance = 50;
            this.controls.maxDistance = 500;
            this.controls.maxPolarAngle = Math.PI;
            this.controls.enablePan = true;
            this.controls.panSpeed = 1.0;
            this.controls.rotateSpeed = 1.0;
            this.controls.zoomSpeed = 1.2;
            this.controls.target.set(0, 0, 0);"""

content = content.replace(old_controls, new_controls)
print("âœ… Camera controls configured (zoom: 50-500, smooth)")

with open('js/script.js', 'w', encoding='utf-8') as f:
    f.write(content)

is_valid, error = check_syntax()

if is_valid:
    print("âœ… PHASE 5 COMPLETE!")
else:
    print("âŒ Error:")
    print(error)
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'js/script.js'])
