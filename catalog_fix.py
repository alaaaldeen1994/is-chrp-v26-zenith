import os
import re

def fix_catalog():
    path = 'technical_catalog.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fuzzy match for Neural SDE section
    pattern = r'(<div class="text-rose-400 font-bold mb-1">Neural SDEs \(Infinite-GAN\)</div>\s+<p class="text-slate-400 leading-relaxed">)(.*?)(</p>\s+<div class="text-\[10px\] text-slate-500 mt-2 italic">)(.*?)(</div>)'
    
    replacement = r'<div class="text-rose-400 font-bold mb-1">Neural SDEs (Stochastic Latent Drift)</div>\n                            <p class="text-slate-400 leading-relaxed">Models cell-state evolution as continuous-time stochastic processes using scVI latent manifolds. The engine explicitly separates the Deterministic Drift coefficient (f) from the Stochastic Diffusion coefficient (g), enabling biologically realistic temporal predictions grounded in SDE theory.</p>\n                            <div class="text-[10px] text-slate-500 mt-2 italic">Refined scVI-SDE Integration (v27.0 GOLD).</div>'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        print("Updated SDE section via Regex.")
    else:
        print("SDE section Regex failed.")
        
    # Remove DriftMLP reference
    target_driftmlp = 'Wait for "TRAINED DriftMLP weights loaded!"'
    replacement_driftmlp = 'Wait for "Stochastic Latent Drift Engine (scVI) initialized!"'
    new_content = new_content.replace(target_driftmlp, replacement_driftmlp)
    
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_content)
    print("Catalog updated successfully.")

if __name__ == "__main__":
    fix_catalog()
