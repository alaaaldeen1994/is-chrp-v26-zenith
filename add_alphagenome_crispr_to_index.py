import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
idx_path = os.path.join(base, 'index.html')

with open(idx_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

target_sec3 = """                <!-- SECTION 3: Genomic Knockout -->
                <div style="padding:10px 10px 8px;border-bottom:1px solid rgba(255,255,255,0.04);">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;">
                        <div style="font-size:8px;color:#3b82f6;font-weight:900;letter-spacing:0.08em;text-transform:uppercase;display:flex;align-items:center;gap:4px;">
                            <i data-lucide="scissors" class="w-2.5 h-2.5"></i> 3. Genomic Knockout
                        </div>
                        <span style="font-size:6px;color:#60a5fa;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.2);padding:2px 6px;border-radius:20px;font-weight:700;">Stress Test</span>
                    </div>
                    <select id="knockout-gene-sel" class="w-full bg-black/60 border border-blue-500/20 text-[9px] py-1.5 px-2 rounded-lg outline-none focus:border-blue-500/50 mb-2 text-slate-300" style="margin-bottom:6px;">
                        <option value="50">TP53 (Tumor Suppressor)</option>
                        <option value="0">POU5F1 (OCT4 - Stemness)</option>
                        <option value="1">SOX2 (Pluripotency)</option>
                        <option value="2">NANOG (Maintenance)</option>
                        <option value="11">GATA4 (Cardiac Pioneer)</option>
                        <option value="22">PAX6 (Neural Master)</option>
                        <option value="51">MKI67 (Proliferation)</option>
                    </select>
                    <button onclick="BiosimLab.applyKnockout()" class="w-full h-7 flex items-center justify-center gap-1.5 bg-blue-600/20 hover:bg-blue-600/35 border border-blue-500/40 text-blue-400 text-[8px] font-black uppercase tracking-widest rounded-lg transition-all">
                        <i data-lucide="scissors" class="w-3 h-3"></i> Apply Knockout
                    </button>
                    <div id="active-knockouts" class="mt-2 flex flex-wrap gap-1"></div>
                </div>"""

new_sec3 = """                <!-- SECTION 3: Genomic Knockout & AlphaGenome CRISPR Engine -->
                <div style="padding:10px 10px 8px;border-bottom:1px solid rgba(255,255,255,0.04);">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;">
                        <div style="font-size:8px;color:#3b82f6;font-weight:900;letter-spacing:0.08em;text-transform:uppercase;display:flex;align-items:center;gap:4px;">
                            <i data-lucide="scissors" class="w-2.5 h-2.5"></i> 3. CRISPR & ALPHAGENOME
                        </div>
                        <span style="font-size:6px;color:#60a5fa;background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.2);padding:2px 6px;border-radius:20px;font-weight:700;">98% Non-Coding AI</span>
                    </div>
                    <select id="knockout-gene-sel" class="w-full bg-black/60 border border-blue-500/20 text-[9px] py-1.5 px-2 rounded-lg outline-none focus:border-blue-500/50 mb-2 text-slate-300" style="margin-bottom:6px;">
                        <option value="50">TP53 (Tumor Suppressor)</option>
                        <option value="0">POU5F1 (OCT4 - Stemness)</option>
                        <option value="1">SOX2 (Pluripotency)</option>
                        <option value="2">NANOG (Maintenance)</option>
                        <option value="11">GATA4 (Cardiac Pioneer)</option>
                        <option value="22">PAX6 (Neural Master)</option>
                        <option value="51">MKI67 (Proliferation)</option>
                    </select>
                    <button onclick="BiosimLab.applyKnockout()" class="w-full h-7 flex items-center justify-center gap-1.5 bg-blue-600/20 hover:bg-blue-600/35 border border-blue-500/40 text-blue-400 text-[8px] font-black uppercase tracking-widest rounded-lg transition-all mb-2">
                        <i data-lucide="scissors" class="w-3 h-3"></i> Apply Knockout
                    </button>
                    <div id="active-knockouts" class="mt-1 mb-2 flex flex-wrap gap-1"></div>

                    <!-- ALPHAGENOME 98% NON-CODING CRISPR AUDIT CONSOLE -->
                    <div class="mt-2 pt-2 border-t border-blue-900/30 bg-blue-950/30 p-2 rounded-lg border border-blue-500/20">
                        <div class="text-[8px] font-black text-blue-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <i data-lucide="cpu" class="w-3 h-3 text-indigo-400"></i> AlphaGenome 98% Non-Coding AI
                        </div>
                        <div class="text-[7px] text-slate-400 mb-2">Decode 98% non-coding genome & generate CRISPR repair sgRNA.</div>
                        <input id="alphagenome-variant-input" type="text" value="chr12:111,842,901 C>T" class="w-full bg-black/80 border border-blue-500/30 text-[8px] py-1 px-2 rounded font-mono text-blue-300 mb-1.5 outline-none focus:border-blue-400" placeholder="e.g. chr12:111,842,901 C>T">
                        <button onclick="runAlphaGenomeVariantAudit()" class="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-[8px] font-black uppercase tracking-wider rounded transition-all shadow-md shadow-indigo-900/30 flex items-center justify-center gap-1">
                            <i data-lucide="sparkles" class="w-3 h-3"></i> AUDIT NON-CODING & GENERATE CRISPR
                        </button>
                        <div id="alphagenome-result-card" class="hidden mt-2 p-2 bg-slate-900/90 border border-indigo-500/40 rounded text-[7.5px] font-mono space-y-1"></div>
                    </div>
                </div>"""

if target_sec3 in content:
    content = content.replace(target_sec3, new_sec3)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Integrated AlphaGenome CRISPR Console into index.html Section 3!")
else:
    print("WARNING: target_sec3 not matched in index.html")

res = subprocess.run(['python', 'check_inline_scripts.py'], capture_output=True, text=True, cwd=base)
print("check_inline_scripts output:")
print(res.stdout)
