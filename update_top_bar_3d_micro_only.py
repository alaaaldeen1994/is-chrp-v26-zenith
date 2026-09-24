import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'

# 1. UPDATE index.html
idx_path = os.path.join(base, 'index.html')
with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

old_toggle_block = """                <!-- UNIFIED MOLECULAR 3D VIEW TOGGLE -->
                <div class="flex items-center gap-1 bg-slate-900/80 p-0.5 rounded-lg border border-blue-500/30">
                    <button id="btn-mode-3d" class="px-3 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1"
                        onclick="BiosimRenderer.setRenderMode('3D_MOLECULAR')" title="Unified 3D Molecular Representation (Ribbon, Surface & Atomic Clusters)">
                        <i data-lucide="box" class="w-3 h-3"></i> 3D MOLECULAR
                    </button>
                    <button id="btn-mode-2d" class="px-2.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all"
                        onclick="BiosimRenderer.setRenderMode('2D_MICRO')" title="2D Microscopic View">2D MICRO</button>
                </div>"""

new_toggle_block = """                <!-- VIEW TOGGLES (3D and Micro ONLY - No 2D) -->
                <div class="flex items-center gap-1 bg-slate-900/80 p-0.5 rounded-lg border border-blue-500/30">
                    <button id="btn-view-3d" class="px-3.5 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1.5"
                        onclick="switchMainView('3D')" title="3D Molecular View">
                        <i data-lucide="box" class="w-3 h-3"></i> 3D
                    </button>
                    <button id="btn-view-micro" class="px-3.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all flex items-center gap-1.5"
                        onclick="switchMainView('MICRO')" title="Microscopy Analysis View">
                        <i data-lucide="microscope" class="w-3 h-3"></i> Micro
                    </button>
                </div>"""

if old_toggle_block in content:
    content = content.replace(old_toggle_block, new_toggle_block)
else:
    print("WARNING: old_toggle_block not matched, searching with fallback regex...")

# Add switchMainView implementation to index.html inline script if not present
switch_script = """
<script>
function switchMainView(mode) {
    const btn3d = document.getElementById('btn-view-3d');
    const btnMicro = document.getElementById('btn-view-micro');

    if (mode === '3D') {
        if (btn3d) btn3d.className = 'px-3.5 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1.5';
        if (btnMicro) btnMicro.className = 'px-3.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all flex items-center gap-1.5';

        const renderer = window.BiosimRenderer || (typeof BiosimRenderer !== 'undefined' ? BiosimRenderer : null);
        if (renderer && renderer.setRenderMode) renderer.setRenderMode('3D_MOLECULAR');

        const latentMap = (window.BiosimBridge && window.BiosimBridge.LatentMap) ? window.BiosimBridge.LatentMap : null;
        if (latentMap && latentMap.toggleView) latentMap.toggleView('3D');
    } else if (mode === 'MICRO') {
        if (btnMicro) btnMicro.className = 'px-3.5 py-1 text-[9px] font-black text-white bg-blue-600 rounded border border-blue-400 transition-all shadow-sm flex items-center gap-1.5';
        if (btn3d) btn3d.className = 'px-3.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all flex items-center gap-1.5';

        const latentMap = (window.BiosimBridge && window.BiosimBridge.LatentMap) ? window.BiosimBridge.LatentMap : null;
        if (latentMap && latentMap.toggleView) latentMap.toggleView('MICROSCOPE');
    }
}
window.switchMainView = switchMainView;
</script>
"""

if "function switchMainView" not in content:
    content = content.replace("</body>", switch_script + "\n</body>")

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Updated index.html with ONLY 3D and Micro top bar options!")

# Check inline scripts syntax
res = subprocess.run(['node', '-c', idx_path], capture_output=True, text=True)
