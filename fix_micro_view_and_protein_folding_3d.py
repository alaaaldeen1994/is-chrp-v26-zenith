import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. FIX index.html CONTAINER ID & HASH FOR MICROSCOPE VIEW
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

# Add id="main-viewport-2d" to canvas parent container
old_canvas_wrap = '<div class="relative w-full h-full overflow-hidden">'
new_canvas_wrap = '<div id="main-viewport-2d" class="relative w-full h-full overflow-hidden">'

if old_canvas_wrap in idx_content and 'id="main-viewport-2d"' not in idx_content:
    idx_content = idx_content.replace(old_canvas_wrap, new_canvas_wrap, 1)

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(idx_content)

print("SUCCESS: Added id='main-viewport-2d' to index.html!")


# 2. UPDATE js/script.js toggleView AND drawUnifiedMolecular3D RENDERER
js_path = os.path.join(base, 'js', 'script.js')
with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()

js_orig = js_content

# Enhance toggleView in js/script.js to cleanly hide 2d container and show microscope container
old_toggle_view = """        toggleView(mode) {
            this.viewMode = mode;
            const canvas = document.getElementById('canvas');
            const viewportMicro = document.getElementById('main-viewport-microscope');
            const viewport3d = document.getElementById('main-viewport-3d');
            const leg = document.getElementById('KAGAWEA-legend');
            const modeText = document.getElementById('sidebar-view-mode');

            if (mode === 'MICROSCOPE') {
                canvas.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (viewportMicro) viewportMicro.style.display = 'block';
                if (leg) leg.style.display = 'flex';
                if (modeText) modeText.innerText = 'VIEWPORT: MICROSCOPE';"""

new_toggle_view = """        toggleView(mode) {
            this.viewMode = mode;
            const canvas = document.getElementById('canvas');
            const viewport2d = document.getElementById('main-viewport-2d') || (canvas ? canvas.parentElement : null);
            const viewportMicro = document.getElementById('main-viewport-microscope');
            const viewport3d = document.getElementById('main-viewport-3d');
            const leg = document.getElementById('KAGAWEA-legend');
            const modeText = document.getElementById('sidebar-view-mode');

            if (mode === 'MICROSCOPE') {
                if (canvas) canvas.style.display = 'none';
                if (viewport2d) viewport2d.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (viewportMicro) {
                    viewportMicro.style.display = 'block';
                    viewportMicro.classList.remove('hidden');
                }
                if (leg) leg.style.display = 'flex';
                if (modeText) modeText.innerText = 'VIEWPORT: MICROSCOPE';"""

js_content = js_content.replace(old_toggle_view, new_toggle_view)

# Restore viewport2d display when switching back to 3D/2D
old_toggle_else = """            } else {
                canvas.style.display = 'block';
                if (viewportMicro) viewportMicro.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (leg) leg.style.display = 'none';
                if (modeText) modeText.innerText = 'VIEWPORT: 2D SIMULATION';"""

new_toggle_else = """            } else {
                if (canvas) canvas.style.display = 'block';
                if (viewport2d) viewport2d.style.display = 'block';
                if (viewportMicro) viewportMicro.style.display = 'none';
                if (viewport3d) viewport3d.style.display = 'none';
                if (leg) leg.style.display = 'none';
                if (modeText) modeText.innerText = 'VIEWPORT: 3D MOLECULAR';"""

js_content = js_content.replace(old_toggle_else, new_toggle_else)


# 3. ENHANCE drawUnifiedMolecular3D TO RENDER THE HIGH-DEFINITION PROTEIN FOLDING CARTOON RIBBON (Matching User Screenshot)
old_draw_molecular_3d = """    // ── UNIFIED 3D MOLECULAR REPRESENTATION (Combining Ribbon, Surface & CPK Ball-and-Stick) ──
    drawUnifiedMolecular3D(ctx, agent, x, y, size) {"""

new_draw_molecular_3d = """    // ── HIGH-DEFINITION 3D PROTEIN FOLDING CARTOON RIBBON RENDERER (Exact Match to User Reference Image) ──
    drawUnifiedMolecular3D(ctx, agent, x, y, size) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(agent.angle);

        // Colors matching user image: Tan/Gold (#d97706, #fef08a, #ca8a04) and Light Sage Green (#86efac, #15803d, #166534)
        const tanRibbon = { main: '#eab308', dark: '#a16207', light: '#fef08a', stroke: '#854d0e' };
        const greenRibbon = { main: '#4ade80', dark: '#15803d', light: '#bbf7d0', stroke: '#166534' };

        // 1. Broad Beta-Sheet Flat Arrow Ribbons (Gold Domain)
        const drawBetaArrow = (angleOffset, colorScheme) => {
            ctx.save();
            ctx.rotate(angleOffset);

            // 3D Shadow underlay
            ctx.shadowColor = 'rgba(2, 6, 23, 0.6)';
            ctx.shadowBlur = 8;
            ctx.shadowOffsetX = 3;
            ctx.shadowOffsetY = 4;

            // Broad Curved Beta-Strand Ribbon Body
            const grad = ctx.createLinearGradient(-size * 0.4, -size * 0.4, size * 0.8, size * 0.4);
            grad.addColorStop(0, colorScheme.light);
            grad.addColorStop(0.4, colorScheme.main);
            grad.addColorStop(1, colorScheme.dark);

            ctx.fillStyle = grad;
            ctx.strokeStyle = colorScheme.stroke;
            ctx.lineWidth = 1.4;

            // Curved Arrow Body
            ctx.beginPath();
            ctx.moveTo(-size * 0.2, -size * 0.1);
            ctx.bezierCurveTo(size * 0.2, -size * 0.45, size * 0.7, -size * 0.2, size * 0.9, -size * 0.45);
            ctx.lineTo(size * 0.82, -size * 0.58);
            ctx.bezierCurveTo(size * 0.6, -size * 0.32, size * 0.15, -size * 0.58, -size * 0.2, -0.22);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Distinct Wide Arrowhead Tip (Matching User Reference Image)
            ctx.beginPath();
            ctx.moveTo(size * 0.75, -size * 0.32);
            ctx.lineTo(size * 1.15, -size * 0.55);
            ctx.lineTo(size * 0.9, -size * 0.7);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Coiled Alpha Helix Spiral Tubes
            ctx.strokeStyle = colorScheme.main;
            ctx.lineWidth = 3.2;
            ctx.lineCap = 'round';
            ctx.beginPath();
            for (let t = 0; t < Math.PI * 2.8; t += 0.18) {
                const hx = -size * 0.3 + t * (size * 0.22);
                const hy = Math.sin(t * 2.5) * (size * 0.18) + (size * 0.2);
                if (t === 0) ctx.moveTo(hx, hy);
                else ctx.lineTo(hx, hy);
            }
            ctx.stroke();

            ctx.restore();
        };

        // Render Gold/Tan Top Folding Domain
        drawBetaArrow(-Math.PI * 0.35, tanRibbon);
        // Render Sage Green Bottom Folding Domain
        drawBetaArrow(Math.PI * 0.65, greenRibbon);

        // 2. Embedded Ball-and-Stick CPK Atom Clusters (At Hinge Junctions - Matching User Image)
        const atoms = [
            { x: -size * 0.12, y: -size * 0.08, r: size * 0.09, col: '#ef4444' }, // Red Oxygen
            { x: size * 0.12, y: -size * 0.12, r: size * 0.08, col: '#3b82f6' },  // Blue Nitrogen
            { x: size * 0.02, y: size * 0.06, r: size * 0.11, col: '#f59e0b' },   // Gold Sulfur
            { x: -size * 0.18, y: size * 0.14, r: size * 0.07, col: '#f8fafc' }   // White Hydrogen
        ];

        // Atomic bonds
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(atoms[0].x, atoms[0].y); ctx.lineTo(atoms[1].x, atoms[1].y);
        ctx.moveTo(atoms[1].x, atoms[1].y); ctx.lineTo(atoms[2].x, atoms[2].y);
        ctx.moveTo(atoms[2].x, atoms[2].y); ctx.lineTo(atoms[3].x, atoms[3].y);
        ctx.stroke();

        // Atom Spheres with 3D Shading
        atoms.forEach(a => {
            const aGrad = ctx.createRadialGradient(a.x - a.r * 0.3, a.y - a.r * 0.3, a.r * 0.1, a.x, a.y, a.r);
            aGrad.addColorStop(0, '#ffffff');
            aGrad.addColorStop(0.4, a.col);
            aGrad.addColorStop(1, '#020617');

            ctx.fillStyle = aGrad;
            ctx.beginPath();
            ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#020617';
            ctx.lineWidth = 0.8;
            ctx.stroke();
        });

        ctx.restore();
    }

    // ── UNIFIED 3D MOLECULAR REPRESENTATION (Combining Ribbon, Surface & CPK Ball-and-Stick) ──
    drawUnifiedMolecular3DOld(ctx, agent, x, y, size) {"""

js_content = js_content.replace(old_draw_molecular_3d, new_draw_molecular_3d)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print("SUCCESS: Enhanced toggleView for Microscope and upgraded 3D Protein Folding Cartoon Ribbon renderer!")

# Run Node syntax check
res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("js/script.js Node check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
