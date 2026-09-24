import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. UPDATE index.html TOP BAR
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    idx_content = f.read()

idx_orig = idx_content

old_toggles_block = """                <!-- MOLECULAR 3D VIEW TOGGLES (Ribbon, Surface, CPK, 2D) -->
                <div class="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-blue-500/30">
                    <button id="btn-mode-ribbon" class="px-2.5 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm"
                        onclick="BiosimRenderer.setRenderMode('RIBBON_3D')" title="3D Cartoon Ribbon (AlphaFold / Antibody Ribbons)">Ribbon 3D</button>
                    <button id="btn-mode-surface" class="px-2.5 py-1 text-[9px] font-black text-slate-300 hover:text-white bg-transparent rounded border border-transparent transition-all"
                        onclick="BiosimRenderer.setRenderMode('SURFACE_3D')" title="3D Volumetric Surface Contours">Surface 3D</button>
                    <button id="btn-mode-cpk" class="px-2.5 py-1 text-[9px] font-black text-slate-300 hover:text-white bg-transparent rounded border border-transparent transition-all"
                        onclick="BiosimRenderer.setRenderMode('CPK_ATOMIC')" title="CPK Atomic Spheres Model">CPK Spheres</button>
                    <button id="btn-mode-2d" class="px-2.5 py-1 text-[9px] font-black text-slate-300 hover:text-white bg-transparent rounded border border-transparent transition-all"
                        onclick="BiosimRenderer.setRenderMode('SPHERE')" title="2D Micro View">2D Micro</button>
                </div>"""

new_single_toggle = """                <!-- UNIFIED MOLECULAR 3D VIEW TOGGLE -->
                <div class="flex items-center gap-1 bg-slate-900/80 p-0.5 rounded-lg border border-blue-500/30">
                    <button id="btn-mode-3d" class="px-3 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1"
                        onclick="BiosimRenderer.setRenderMode('3D_MOLECULAR')" title="Unified 3D Molecular Representation (Ribbon, Surface & Atomic Clusters)">
                        <i data-lucide="box" class="w-3 h-3"></i> 3D MOLECULAR
                    </button>
                    <button id="btn-mode-2d" class="px-2.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all"
                        onclick="BiosimRenderer.setRenderMode('2D_MICRO')" title="2D Microscopic View">2D MICRO</button>
                </div>"""

if old_toggles_block in idx_content:
    idx_content = idx_content.replace(old_toggles_block, new_single_toggle)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(idx_content)
    print("SUCCESS: Unified top bar controls into single '3D MOLECULAR' option in index.html!")
else:
    print("WARNING: Old toggles block not found in index.html")

# 2. UPDATE BiosimRenderer IN js/script.js TO RENDER UNIFIED 3D MOLECULAR COMPLEX
js_path = os.path.join(base, 'js', 'script.js')
with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
    js_content = f.read()

js_orig = js_content

# Update BiosimRenderer setRenderMode and drawCell for UNIFIED 3D_MOLECULAR mode
old_renderer_impl = """const BiosimRenderer = {
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
    },"""

new_renderer_impl = """const BiosimRenderer = {
    mode: '3D_MOLECULAR', // 3D_MOLECULAR (Unified), 2D_MICRO
    showHeatmap: false,

    setRenderMode(newMode) {
        this.mode = newMode;
        if (typeof BiosimUI !== 'undefined' && BiosimUI.notify) {
            BiosimUI.notify('Molecular View', `Mode: ${newMode === '3D_MOLECULAR' ? '3D Molecular Representation' : '2D Micro'}`, 'suc');
        }
        const btn3d = document.getElementById('btn-mode-3d');
        const btn2d = document.getElementById('btn-mode-2d');
        if (btn3d && btn2d) {
            if (newMode === '3D_MOLECULAR') {
                btn3d.className = 'px-3 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1';
                btn2d.className = 'px-2.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all';
            } else {
                btn2d.className = 'px-3 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1';
                btn3d.className = 'px-2.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all';
            }
        }
    },

    toggleStyle() {
        this.setRenderMode(this.mode === '3D_MOLECULAR' ? '2D_MICRO' : '3D_MOLECULAR');
    },

    drawCell(ctx, agent, x, y, size) {
        if (!agent.angle) agent.angle = (agent.id * 0.77) % (Math.PI * 2);
        agent.angle += 0.012; // Continuous 3D rotation

        if (this.mode === '3D_MOLECULAR') {
            this.drawUnifiedMolecular3D(ctx, agent, x, y, size * 2.2);
        } else {
            this.drawSphere2D(ctx, agent, x, y, size);
        }
    },

    // ── UNIFIED 3D MOLECULAR REPRESENTATION (Combining Ribbon, Surface & CPK Ball-and-Stick) ──
    drawUnifiedMolecular3D(ctx, agent, x, y, size) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(agent.angle);

        // 1. Subtle Molecular Surface Contour Underlay (Volumetric Soft Surface)
        const drawSurfaceDomain = (ox, oy, radius, colorHex) => {
            const grad = ctx.createRadialGradient(ox - radius * 0.3, oy - radius * 0.3, radius * 0.1, ox, oy, radius * 1.2);
            grad.addColorStop(0, 'rgba(255, 255, 255, 0.7)');
            grad.addColorStop(0.4, colorHex);
            grad.addColorStop(1, 'rgba(3, 15, 38, 0.8)');

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(ox, oy, radius, 0, Math.PI * 2);
            ctx.fill();
        };

        drawSurfaceDomain(-size * 0.45, -size * 0.35, size * 0.32, 'rgba(244, 63, 94, 0.4)');  // Fab Left (Rose Pink Surface)
        drawSurfaceDomain(size * 0.45, -size * 0.35, size * 0.32, 'rgba(234, 179, 8, 0.4)');   // Fab Right (Gold Yellow Surface)
        drawSurfaceDomain(0, size * 0.4, size * 0.35, 'rgba(16, 185, 129, 0.4)');              // Fc Stem (Emerald Green Surface)

        // 2. Cartoon Ribbon Overlay (Beta Strands & Alpha Helices)
        const drawChainRibbon = (angleOffset, ribbonColor, darkColor) => {
            ctx.save();
            ctx.rotate(angleOffset);

            // Beta Strand Arrow Ribbon
            ctx.fillStyle = ribbonColor;
            ctx.strokeStyle = darkColor;
            ctx.lineWidth = 1.2;

            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.bezierCurveTo(size * 0.3, -size * 0.2, size * 0.6, -size * 0.1, size * 0.8, -size * 0.3);
            ctx.lineTo(size * 0.75, -size * 0.38);
            ctx.bezierCurveTo(size * 0.55, -size * 0.18, size * 0.28, -size * 0.26, 0, -0.08);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Beta Strand Arrow Tip
            ctx.beginPath();
            ctx.moveTo(size * 0.6, -size * 0.25);
            ctx.lineTo(size * 0.9, -size * 0.45);
            ctx.lineTo(size * 0.7, -size * 0.52);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // Alpha Helix Coiled Loops
            ctx.strokeStyle = ribbonColor;
            ctx.lineWidth = 2.4;
            ctx.lineCap = 'round';
            ctx.beginPath();
            for (let t = 0; t < Math.PI * 2.2; t += 0.2) {
                const hx = size * 0.2 + t * (size * 0.16);
                const hy = Math.sin(t * 3) * (size * 0.12) + (size * 0.15);
                if (t === 0) ctx.moveTo(hx, hy);
                else ctx.lineTo(hx, hy);
            }
            ctx.stroke();

            ctx.restore();
        };

        drawChainRibbon(-Math.PI * 0.7, '#fda4af', '#e11d48'); // Left Arm (Rose Pink Ribbon)
        drawChainRibbon(-Math.PI * 0.1, '#fde047', '#ca8a04'); // Right Arm (Gold Yellow Ribbon)
        drawChainRibbon(Math.PI * 0.5, '#6ee7b7', '#059669');  // Stem (Emerald Green Ribbon)

        // 3. Ball-and-Stick CPK Ligand Cluster (At Core Hinge)
        const cpkAtoms = [
            { x: -size * 0.1, y: -size * 0.05, r: size * 0.09, col: '#ef4444' }, // Oxygen
            { x: size * 0.1, y: -size * 0.08, r: size * 0.08, col: '#3b82f6' },  // Nitrogen
            { x: 0, y: size * 0.1, r: size * 0.10, col: '#f59e0b' },              // Sulfur Hinge
            { x: size * 0.08, y: size * 0.16, r: size * 0.06, col: '#ffffff' }   // Hydrogen
        ];

        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(cpkAtoms[0].x, cpkAtoms[0].y); ctx.lineTo(cpkAtoms[1].x, cpkAtoms[1].y);
        ctx.moveTo(cpkAtoms[1].x, cpkAtoms[1].y); ctx.lineTo(cpkAtoms[2].x, cpkAtoms[2].y);
        ctx.moveTo(cpkAtoms[2].x, cpkAtoms[2].y); ctx.lineTo(cpkAtoms[3].x, cpkAtoms[3].y);
        ctx.stroke();

        cpkAtoms.forEach(a => {
            ctx.fillStyle = a.col;
            ctx.beginPath();
            ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#020617';
            ctx.lineWidth = 0.6;
            ctx.stroke();
        });

        ctx.restore();
    },"""

if old_renderer_impl in js_content:
    js_content = js_content.replace(old_renderer_impl, new_renderer_impl)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("SUCCESS: Unified BiosimRenderer into single 3D_MOLECULAR mode in js/script.js!")
else:
    print("WARNING: Old renderer impl block not matched in js/script.js")

# Check Node syntax
res = subprocess.run(['node', '-c', js_path], capture_output=True, text=True)
print("Node syntax check exit code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr)
else:
    print("SYNTAX 100% PERFECT!")
