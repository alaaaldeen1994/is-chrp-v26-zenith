import os, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. UPGRADE BiosimRenderer in js/script.js
js_path = os.path.join(base, 'js', 'script.js')
with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()

js_orig = js_content

# Upgrade BiosimRenderer definition to include Molecular 3D Render Modes matching user images
old_renderer = """const BiosimRenderer = {
    mode: 'FLUORO', // FLUORO, PHASE, IMMUNO
    showHeatmap: false,

    toggleStyle() {
        const modes = ['FLUORO', 'PHASE', 'IMMUNO'];
        let idx = modes.indexOf(this.mode);
        this.mode = modes[(idx + 1) % modes.length];
        BiosimUI.notify('Display', `Mode switched to ${this.mode}`, 'inf');
    },

    drawCell(ctx, agent, x, y, size) {"""

new_renderer = """const BiosimRenderer = {
    mode: 'RIBBON_3D', // RIBBON_3D, SURFACE_3D, CPK_ATOMIC, SPHERE
    showHeatmap: false,

    setRenderMode(newMode) {
        this.mode = newMode;
        if (typeof BiosimUI !== 'undefined' && BiosimUI.notify) {
            BiosimUI.notify('Molecular View', `Render Mode: ${newMode.replace('_', ' ')}`, 'suc');
        }
        // Update top bar mode button styles
        const btns = ['btn-mode-ribbon', 'btn-mode-surface', 'btn-mode-cpk', 'btn-mode-2d'];
        btns.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                if ((id === 'btn-mode-ribbon' && newMode === 'RIBBON_3D') ||
                    (id === 'btn-mode-surface' && newMode === 'SURFACE_3D') ||
                    (id === 'btn-mode-cpk' && newMode === 'CPK_ATOMIC') ||
                    (id === 'btn-mode-2d' && newMode === 'SPHERE')) {
                    btn.classList.add('bg-blue-600', 'text-white', 'border-blue-400');
                    btn.classList.remove('bg-transparent', 'text-slate-400', 'border-white/10');
                } else {
                    btn.classList.remove('bg-blue-600', 'text-white', 'border-blue-400');
                    btn.classList.add('bg-transparent', 'text-slate-400', 'border-white/10');
                }
            }
        });
    },

    toggleStyle() {
        const modes = ['RIBBON_3D', 'SURFACE_3D', 'CPK_ATOMIC', 'SPHERE'];
        let idx = modes.indexOf(this.mode);
        this.setRenderMode(modes[(idx + 1) % modes.length]);
    },

    drawCell(ctx, agent, x, y, size) {
        if (!agent.angle) agent.angle = (agent.id * 0.77) % (Math.PI * 2);
        agent.angle += 0.012; // Continuous 3D rotation

        if (this.mode === 'RIBBON_3D') {
            this.drawRibbon3D(ctx, agent, x, y, size * 2.2);
        } else if (this.mode === 'SURFACE_3D') {
            this.drawSurface3D(ctx, agent, x, y, size * 2.4);
        } else if (this.mode === 'CPK_ATOMIC') {
            this.drawCPKAtomic(ctx, agent, x, y, size * 2.2);
        } else {
            this.drawSphere2D(ctx, agent, x, y, size);
        }
    },

    // ── 3D MOLECULAR RIBBON CARTOON (Matching Image 3 & 4) ──
    drawRibbon3D(ctx, agent, x, y, size) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(agent.angle);

        // Pastel color scheme matching user reference images
        const colors = {
            pink: { ribbon: '#fda4af', dark: '#e11d48', glow: 'rgba(244,63,94,0.3)' },
            yellow: { ribbon: '#fde047', dark: '#ca8a04', glow: 'rgba(234,179,8,0.3)' },
            green: { ribbon: '#6ee7b7', dark: '#059669', glow: 'rgba(16,185,129,0.3)' }
        };

        const drawChain = (angleOffset, colorScheme, isDouble) => {
            ctx.save();
            ctx.rotate(angleOffset);

            // Back glow
            ctx.shadowColor = colorScheme.glow;
            ctx.shadowBlur = 12;

            // Beta Strand 1 (Flat Arrow Ribbon)
            ctx.fillStyle = colorScheme.ribbon;
            ctx.strokeStyle = colorScheme.dark;
            ctx.lineWidth = 1.2;

            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.bezierCurveTo(size * 0.3, -size * 0.2, size * 0.6, -size * 0.1, size * 0.8, -size * 0.3);
            ctx.lineTo(size * 0.75, -size * 0.38);
            ctx.bezierCurveTo(size * 0.55, -size * 0.18, size * 0.28, -size * 0.26, 0, -0.08);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Beta Strand 2 (Arrow Tip)
            ctx.beginPath();
            ctx.moveTo(size * 0.6, -size * 0.25);
            ctx.lineTo(size * 0.9, -size * 0.45);
            ctx.lineTo(size * 0.7, -size * 0.52);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Alpha Helix Coiled Ribbon Loop
            ctx.strokeStyle = colorScheme.ribbon;
            ctx.lineWidth = 2.5;
            ctx.lineCap = 'round';
            ctx.beginPath();
            for (let t = 0; t < Math.PI * 2.5; t += 0.2) {
                const hx = size * 0.2 + t * (size * 0.18);
                const hy = Math.sin(t * 3) * (size * 0.12) + (size * 0.15);
                if (t === 0) ctx.moveTo(hx, hy);
                else ctx.lineTo(hx, hy);
            }
            ctx.stroke();

            // Ball and Stick Atomic Ligand Clusters (matching Image 5)
            if (isDouble) {
                const atoms = [
                    { x: size * 0.45, y: size * 0.1, r: size * 0.08, col: '#ef4444' }, // Oxygen (Red)
                    { x: size * 0.55, y: size * 0.18, r: size * 0.07, col: '#3b82f6' }, // Nitrogen (Blue)
                    { x: size * 0.38, y: size * 0.22, r: size * 0.09, col: '#f59e0b' }, // Sulfur (Yellow)
                    { x: size * 0.48, y: size * 0.28, r: size * 0.06, col: '#ffffff' }  # Hydrogen (White)
                ];

                // Bonds
                ctx.strokeStyle = '#94a3b8';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(atoms[0].x, atoms[0].y); ctx.lineTo(atoms[1].x, atoms[1].y);
                ctx.moveTo(atoms[1].x, atoms[1].y); ctx.lineTo(atoms[2].x, atoms[2].y);
                ctx.moveTo(atoms[2].x, atoms[2].y); ctx.lineTo(atoms[3].x, atoms[3].y);
                ctx.stroke();

                // Atom Spheres
                atoms.forEach(a => {
                    ctx.fillStyle = a.col;
                    ctx.beginPath();
                    ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.strokeStyle = '#0f172a';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                });
            }

            ctx.restore();
        };

        // Y-shaped Antibody Structure Assembly (Fab Left, Fab Right, Fc Stem)
        drawChain(-Math.PI * 0.7, colors.pink, true);   // Left Arm (Rose Pink)
        drawChain(-Math.PI * 0.1, colors.yellow, false); // Right Arm (Gold Yellow)
        drawChain(Math.PI * 0.5, colors.green, true);    // Fc Stem (Emerald Green)

        // Hinge Disulfide Center Node
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(0, 0, size * 0.14, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    },

    // ── 3D MOLECULAR SURFACE CONTOURS (Matching Image 2) ──
    drawSurface3D(ctx, agent, x, y, size) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(agent.angle * 0.7);

        const drawBlob = (ox, oy, radius, colorHex, shadowHex) => {
            const grad = ctx.createRadialGradient(ox - radius * 0.3, oy - radius * 0.3, radius * 0.1, ox, oy, radius * 1.3);
            grad.addColorStop(0, '#ffffff');
            grad.addColorStop(0.3, colorHex);
            grad.addColorStop(0.8, shadowHex);
            grad.addColorStop(1, '#020617');

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(ox, oy, radius, 0, Math.PI * 2);
            ctx.fill();
        };

        // Pastel Surface Domains (Y-shaped Assembly)
        drawBlob(-size * 0.5, -size * 0.4, size * 0.38, '#fda4af', '#9f1239'); // Pink Fab
        drawBlob(size * 0.5, -size * 0.4, size * 0.38, '#fde047', '#854d0e');  // Yellow Fab
        drawBlob(0, size * 0.45, size * 0.42, '#6ee7b7', '#065f46');           // Green Fc
        drawBlob(0, 0, size * 0.32, '#cbd5e1', '#334155');                      // Central Domain

        ctx.restore();
    },

    // ── CPK ATOMIC SPHERES MODEL (Matching Image 1) ──
    drawCPKAtomic(ctx, agent, x, y, size) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(agent.angle * 0.5);

        const atomColors = ['#f87171', '#60a5fa', '#facc15', '#4ade80', '#e2e8f0', '#38bdf8'];
        const numAtoms = 16;
        for (let i = 0; i < numAtoms; i++) {
            const aAngle = (i / numAtoms) * Math.PI * 2;
            const dist = (i % 3 === 0) ? size * 0.4 : (i % 2 === 0 ? size * 0.7 : size * 0.2);
            const ax = Math.cos(aAngle) * dist;
            const ay = Math.sin(aAngle) * dist;
            const ar = size * 0.16;

            const grad = ctx.createRadialGradient(ax - ar * 0.3, ay - ar * 0.3, ar * 0.1, ax, ay, ar);
            grad.addColorStop(0, '#ffffff');
            grad.addColorStop(0.4, atomColors[i % atomColors.length]);
            grad.addColorStop(1, '#090d16');

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(ax, ay, ar, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    },

    // ── 2D GLOSSY SPHERE (Classic Fallback) ──
    drawSphere2D(ctx, agent, x, y, size) {
        const type = agent.type;
        const color = CONFIG.colors[type] || CONFIG.colors.SOMATIC;

        ctx.save();
        ctx.translate(x, y);

        const grad = ctx.createRadialGradient(-size * 0.3, -size * 0.3, size * 0.1, 0, 0, size);
        grad.addColorStop(0, '#ffffff');
        grad.addColorStop(0.2, `hsl(${color.h}, ${color.s}%, ${Math.min(100, color.l + 20)}%)`);
        grad.addColorStop(0.5, `hsl(${color.h}, ${color.s}%, ${color.l}%)`);
        grad.addColorStop(1, `hsl(${color.h}, ${color.s}%, ${Math.max(0, color.l - 20)}%)`);

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(0, 0, size, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
    },"""

js_content = js_content.replace(old_renderer, new_renderer)

# Upgrade canvas background rendering in BiosimEngine.loop to LUMINOUS DEEP BLUE GRADIENT matching user images
old_bg_fill = """            // Render
            this.ctx.fillStyle = '#101010'; // v26: Darker lab environment
            this.ctx.fillRect(0, 0, w, h);"""

new_bg_fill = """            // Render: Luminous Deep Ocean Blue Gradient (Matching User Reference Images)
            const bgGrad = this.ctx.createRadialGradient(w / 2, h / 2, 50, w / 2, h / 2, Math.max(w, h) * 0.8);
            bgGrad.addColorStop(0, '#02427a');
            bgGrad.addColorStop(0.4, '#011c3a');
            bgGrad.addColorStop(0.8, '#000e24');
            bgGrad.addColorStop(1, '#000714');
            this.ctx.fillStyle = bgGrad;
            this.ctx.fillRect(0, 0, w, h);"""

js_content = js_content.replace(old_bg_fill, new_bg_fill)

if js_content != js_orig:
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("SUCCESS: Upgraded BiosimRenderer to Molecular 3D Ribbon & Surface Suite in js/script.js!")
else:
    print("WARNING: Could not find old_renderer or old_bg_fill in js/script.js")

# 2. ADD MOLECULAR 3D VIEW TOGGLE BUTTONS IN index.html
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

# Add top controls for 3D Molecular modes
old_top_controls = """<div class="flex items-center gap-2">
                <button onclick="BiosimRenderer.toggleStyle()"
                    class="px-2.5 py-1 bg-black/60 border border-white/10 rounded text-[9px] font-bold text-slate-300 hover:text-white transition-all">2D Micro</button>"""

new_top_controls = """<div class="flex items-center gap-1.5">
                <button id="btn-mode-ribbon" onclick="BiosimRenderer.setRenderMode('RIBBON_3D')"
                    class="px-2.5 py-1 bg-blue-600 border border-blue-400 rounded text-[9px] font-black text-white hover:bg-blue-500 transition-all" title="3D Cartoon Ribbon Representation (Matching AlphaFold / Antibody Ribbons)">Ribbon 3D</button>
                <button id="btn-mode-surface" onclick="BiosimRenderer.setRenderMode('SURFACE_3D')"
                    class="px-2.5 py-1 bg-transparent border border-white/10 rounded text-[9px] font-bold text-slate-400 hover:text-white transition-all" title="Volumetric Molecular Surface Contours">Surface 3D</button>
                <button id="btn-mode-cpk" onclick="BiosimRenderer.setRenderMode('CPK_ATOMIC')"
                    class="px-2.5 py-1 bg-transparent border border-white/10 rounded text-[9px] font-bold text-slate-400 hover:text-white transition-all" title="CPK Atomic Space-Filling Spheres">CPK Spheres</button>
                <button id="btn-mode-2d" onclick="BiosimRenderer.setRenderMode('SPHERE')"
                    class="px-2.5 py-1 bg-transparent border border-white/10 rounded text-[9px] font-bold text-slate-400 hover:text-white transition-all" title="2D Cellular Micro View">2D Micro</button>"""

idx_content = idx_content.replace(old_top_controls, new_top_controls)

if idx_content != idx_orig:
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print("SUCCESS: Added 3D Molecular Mode Control Suite to index.html top bar!")
else:
    print("WARNING: Top controls pattern not matched in index.html, searching alternatives...")

print("DONE!")
