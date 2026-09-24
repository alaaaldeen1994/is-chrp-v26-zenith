import os

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

old_toggles = """                <!-- VIEW TOGGLES -->
                <div class="flex items-center gap-1 bg-white/5 p-0.5 rounded border border-white/10">
                    <button class="px-2 py-1 text-[9px] font-black text-blue-400 bg-blue-600/20 rounded"
                        onclick="BiosimBridge.LatentMap.toggleView('2D')">2D</button>
                    <a href="colony_microscopy_demo.html" class="px-2 py-1 text-[9px] font-black text-slate-400 hover:text-blue-400 transition-all font-bold rounded"
                        >Micro</a>
                </div>"""

new_toggles = """                <!-- MOLECULAR 3D VIEW TOGGLES (Ribbon, Surface, CPK, 2D) -->
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

if old_toggles in content:
    content = content.replace(old_toggles, new_toggles)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Added 3D Molecular Mode Control Suite to index.html!")
else:
    print("WARNING: Old toggles block not found in index.html")
