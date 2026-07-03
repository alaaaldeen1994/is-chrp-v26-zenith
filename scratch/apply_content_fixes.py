import os

base_path = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"

# --- 1. Update technical_catalog.html ---
catalog_path = os.path.join(base_path, "technical_catalog.html")
print("Updating technical_catalog.html...")
with open(catalog_path, "r", encoding="utf-8") as f:
    cat_content = f.read()

# Replacements for technical_catalog.html
cat_replacements = [
    ("5,000-Gene HD", "4,908-Gene HD"),
    ("5,000-dimensional", "4,908-dimensional"),
    ("5000-dimensional", "4,908-dimensional"),
    ("5,000-gene", "4,908-gene"),
    ("5,000+", "4,908"),
    ("5,000-Gene", "4,908-Gene"),
    ("5,000 explicit", "4,908 explicit"),
    ("~5,000 RNA", "4,908 RNA"),
    ("base = torch.rand(N, 5000) * 0.1", "base = torch.rand(N, 4908) * 0.1"),
    ("noise = torch.randn(N, 5000) * sigma", "noise = torch.randn(N, 4908) * sigma"),
    ("5,000+ genes", "4,908 genes"),
    ("(5000D)", "(4,908D)"),
    ("5,000 Genes", "4,908 Genes"),
    ("primary scaling vectors for the IS-CHRP platform.", "primary scaling vectors for the Zenith platform."),
    ("cd /path/to/is-chrp-v27-generative", "cd /path/to/zenith-v30-generative"),
    ("The IS-CHRP Zenith ecosystem", "The Zenith ecosystem"),
]

for orig, repl in cat_replacements:
    cat_content = cat_content.replace(orig, repl)

with open(catalog_path, "w", encoding="utf-8") as f:
    f.write(cat_content)
print("Updated technical_catalog.html.")

# --- 2. Update evidence.html ---
evidence_path = os.path.join(base_path, "evidence.html")
print("Updating evidence.html...")
with open(evidence_path, "r", encoding="utf-8") as f:
    ev_content = f.read()

ev_content = ev_content.replace("5,000 HD", "4,908 HD")

# Replace buttons in evidence.html
btn1_orig = """                <button class="w-full flex items-center justify-between p-6 bg-white rounded-2xl border border-slate-200 hover:border-teal-500/50 hover:shadow-lg transition-all group">
                    <span class="text-xs font-black text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Zenith_v26_training.py</span>
                </button>"""
btn1_repl = """                <button onclick="alert('The training reproduction script is restricted to academic and institutional partners. Please contact info@niluslab.com to request access.')" class="w-full flex items-center justify-between p-6 bg-white rounded-2xl border border-slate-200 hover:border-teal-500/50 hover:shadow-lg transition-all group">
                    <span class="text-xs font-black text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Zenith_v30_training.py</span>
                </button>"""

btn2_orig = """                <button class="w-full flex items-center justify-between p-6 bg-white rounded-2xl border border-slate-200 hover:border-teal-500/50 hover:shadow-lg transition-all group">
                    <span class="text-xs font-black text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Manifold_Validation.log</span>
                </button>"""
btn2_repl = """                <button onclick="alert('The validation log is restricted to academic and institutional partners. Please contact info@niluslab.com to request access.')" class="w-full flex items-center justify-between p-6 bg-white rounded-2xl border border-slate-200 hover:border-teal-500/50 hover:shadow-lg transition-all group">
                    <span class="text-xs font-black text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Manifold_Validation.log</span>
                </button>"""

# Normalise spaces and newlines if they don't match exactly by doing line-based replacement
if btn1_orig in ev_content:
    ev_content = ev_content.replace(btn1_orig, btn1_repl)
else:
    # Try with different newlines or strip
    print("Warning: btn1 exact match not found. Trying flexible replacement.")
    # Let's search line-by-line or fallback
    ev_content = ev_content.replace("Zenith_v26_training.py", "Zenith_v30_training.py")
    # We will locate the button class and replace it
    # We can do this safely via string replace on unique components
    ev_content = ev_content.replace('text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Zenith_v30_training.py</span>', 'text-slate-900 group-hover:text-teal-600 uppercase tracking-widest">Zenith_v30_training.py</span>')

if btn2_orig in ev_content:
    ev_content = ev_content.replace(btn2_orig, btn2_repl)
else:
    print("Warning: btn2 exact match not found. Trying flexible replacement.")

with open(evidence_path, "w", encoding="utf-8") as f:
    f.write(ev_content)
print("Updated evidence.html.")

# --- 3. Update whitepaper.html ---
wp_path = os.path.join(base_path, "whitepaper.html")
print("Updating whitepaper.html...")
with open(wp_path, "r", encoding="utf-8") as f:
    wp_content = f.read()

wp_replacements = [
    ("governing 5,000-gene HD", "governing 4,908-gene HD"),
    ('<div class="spec-value">5,000</div>', '<div class="spec-value">4,908</div>'),
    ("dynamics of 5,000 distinct gene", "dynamics of 4,908 distinct gene"),
    ("utilizes a 5,000-dimensional", "utilizes a 4,908-dimensional"),
    ("gating at 5,000 individual", "gating at 4,908 individual"),
    ("Expansion to 5,000 gene", "Expansion to 4,908 gene"),
    ("5,000 HD Dimensions", "4,908 HD Dimensions"),
]

for orig, repl in wp_replacements:
    wp_content = wp_content.replace(orig, repl)

with open(wp_path, "w", encoding="utf-8") as f:
    f.write(wp_content)
print("Updated whitepaper.html.")

# --- 4. Update regulatory.html ---
reg_path = os.path.join(base_path, "regulatory.html")
print("Updating regulatory.html...")
with open(reg_path, "r", encoding="utf-8") as f:
    reg_content = f.read()

reg_content = reg_content.replace("Mapping (5,000 HD)", "Mapping (4,908 HD)")

with open(reg_path, "w", encoding="utf-8") as f:
    f.write(reg_content)
print("Updated regulatory.html.")

# --- 5. Update about.html ---
about_path = os.path.join(base_path, "about.html")
print("Updating about.html...")
with open(about_path, "r", encoding="utf-8") as f:
    about_content = f.read()

about_replacements = [
    ("5,000-dimensional gene space", "4,908-dimensional gene space"),
    ("capturing 5,000 HD regulatory", "capturing 4,908 HD regulatory"),
]

for orig, repl in about_replacements:
    about_content = about_content.replace(orig, repl)

with open(about_path, "w", encoding="utf-8") as f:
    f.write(about_content)
print("Updated about.html.")

# --- 6. Update trials.html ---
trials_path = os.path.join(base_path, "trials.html")
print("Updating trials.html...")
with open(trials_path, "r", encoding="utf-8") as f:
    tr_content = f.read()

# Add BiosimUI notify definition
ui_def = """
        const BiosimUI = {
            notify(header, message, type) {
                let feed = document.getElementById('toast-feed');
                if (!feed) {
                    feed = document.createElement('div');
                    feed.id = 'toast-feed';
                    feed.style.position = 'fixed';
                    feed.style.bottom = '24px';
                    feed.style.right = '24px';
                    feed.style.zIndex = '9999';
                    feed.style.display = 'flex';
                    feed.style.flexDirection = 'column';
                    feed.style.gap = '8px';
                    document.body.appendChild(feed);
                }
                const toast = document.createElement('div');
                toast.style.background = 'white';
                toast.style.color = '#0f172a';
                toast.style.padding = '12px 16px';
                toast.style.borderRadius = '8px';
                toast.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)';
                toast.style.border = '1px solid #e2e8f0';
                toast.style.minWidth = '240px';
                toast.style.fontSize = '12px';
                toast.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                toast.style.transition = 'all 0.3s ease';
                
                if (type === 'err') toast.style.borderLeft = '4px solid #ef4444';
                else if (type === 'warn') toast.style.borderLeft = '4px solid #f97316';
                else if (type === 'suc') toast.style.borderLeft = '4px solid #10b981';
                else toast.style.borderLeft = '4px solid #3b82f6';
                
                toast.innerHTML = `<div style="font-weight: 700; margin-bottom: 2px;">${header}</div><div style="color: #64748b; font-size: 10px;">${message}</div>`;
                feed.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateY(10px)';
                    setTimeout(() => toast.remove(), 300);
                }, 3000);
            }
        };
"""

# Insert right after <script>
tr_content = tr_content.replace("<script>", f"<script>{ui_def}", 1)

# Replace DEVELOPER_KEY
tr_content = tr_content.replace(
    "'X-API-Key': 'DEVELOPER_KEY'",
    "'X-API-Key': localStorage.getItem('zenith_session_token') || sessionStorage.getItem('zenith_session_token') || 'DEVELOPER_KEY'"
)

with open(trials_path, "w", encoding="utf-8") as f:
    f.write(tr_content)
print("Updated trials.html.")

print("\n=== All 6 files updated successfully! ===")
