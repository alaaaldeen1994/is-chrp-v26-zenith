import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Replace button-based Micro with link-based Micro pointing to colony_microscopy_demo.html
old_micro_btn = """                    <button id="btn-view-micro" class="px-3.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all flex items-center gap-1.5"
                        onclick="switchMainView('MICRO')" title="Microscopy Analysis View">
                        <i data-lucide="microscope" class="w-3 h-3"></i> Micro
                    </button>"""

new_micro_link = """                    <a id="btn-view-micro" href="colony_microscopy_demo.html"
                        class="px-3.5 py-1 text-[9px] font-black text-slate-400 hover:text-white bg-transparent rounded border border-transparent transition-all flex items-center gap-1.5"
                        title="Microscopy Analysis View (Opens Dedicated Page)">
                        <i data-lucide="microscope" class="w-3 h-3"></i> Micro
                    </a>"""

if old_micro_btn in content:
    content = content.replace(old_micro_btn, new_micro_link)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Updated Micro button in index.html to link to colony_microscopy_demo.html!")
else:
    print("WARNING: old_micro_btn not matched in index.html, searching alternatives...")

res = subprocess.run(['python', 'check_inline_scripts.py'], capture_output=True, text=True, cwd=base)
print("check_inline_scripts output:")
print(res.stdout)
