import os, subprocess, re

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Replace print script inside template literal with safe hex escaping
old_print_script = "<' + 'script>window.onload = function() { window.print(); };<' + '/script>"
safe_print_script = "\\x3Cscript\\x3Ewindow.onload = function() { window.print(); };\\x3C/script\\x3E"

content = content.replace(old_print_script, safe_print_script)
content = content.replace("<script>window.onload = function() { window.print(); };</script>", safe_print_script)

# Remove the trailing standalone <script>function switchMainView...</script> at the bottom
standalone_script = """<script>
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
</script>"""

content = content.replace(standalone_script, "")

# Insert switchMainView inside the main window scope functions right after window.printClinicalDossier
clean_switch_func = """
window.switchMainView = function(mode) {
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
};
"""

if "window.switchMainView = function" not in content:
    content = content.replace("window.printClinicalDossier = function() {", clean_switch_func + "\nwindow.printClinicalDossier = function() {")

with open(idx_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Cleaned up script isolation in index.html!")

res = subprocess.run(['python', 'check_inline_scripts.py'], capture_output=True, text=True, cwd=base)
print("check_inline_scripts output:")
print(res.stdout)
