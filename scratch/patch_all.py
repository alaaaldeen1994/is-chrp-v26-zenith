import os

base_dir = r"C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative"

def replace_in_file(filename, old, new):
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Replaced '{old}' with '{new}' in {filename}")

def patch_file(filename, replacements):
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated multiple patterns in {filename}")

bridge_repl = {
    "input_dim=4908": "input_dim=5858",
    "[CurrentGenes(4908)": "[CurrentGenes(5858)",
    "TargetGenes(4908)": "TargetGenes(5858)",
    "486k cells, 14 donors": "2M cells, 83 donors",
    "4908 var_names": "5858 var_names",
    "486k Full HCA Model": "2M Foundation Model",
    "4908-dim": "5858-dim",
    "reshape(n_agents, 4908)": "reshape(n_agents, 5858)",
    "zeros(n_agents, 4908)": "zeros(n_agents, 5858)",
    "state_tensor_4908": "state_tensor_5858",
    "9817": "11717",
    "np.zeros(4908)": "np.zeros(5858)",
    "drift[:, :4908]": "drift[:, :5858]",
    "zeros(4908)": "zeros(5858)",
    "486k model": "2M model",
    "486k Full": "2M Full",
    "scvi_model_486k": "scvi_model_194M",
    "v28_clinical_report.html": "v29_clinical_report.html",
    "v27.0 GOLD": "v29.0 GOLD",
    "v28.0 GOLD": "v29.0 GOLD",
    "V28": "V29",
    "v28": "v29",
    "v27": "v29"
}
patch_file("bridge_server.py", bridge_repl)

html_repl = {
    "v28.0 GOLD GOLD": "v29.0 GOLD",
    "v28.0 GOLD": "v29.0 GOLD",
    "v28.1": "v29.0",
    "v28.0": "v29.0",
    "v28": "v29",
    "v26.4": "v29.0",
    "v26.1": "v29.0",
    "500K": "2M",
    "500,000": "2,000,000",
    "486k": "2M",
    "4,908": "5,858",
    "scvi_model_hca": "zenith_v29_model",
    "Build 0x771A GOLD": "Build 0x290_v29",
    "0xZEN_v26.1_INST_MARCH_992B_COMP": "0xZEN_v29_INST_JUNE_1940K_COMP",
    "v28_clinical_report.html": "v29_clinical_report.html"
}

html_files = [
    "about.html", "evidence.html", "how_it_works.html", "whitepaper.html", 
    "legal.html", "regulatory.html", "contact.html", "trials.html",
    "SCIENTIFIC_SUMMARY.md", "SCIENTIFIC_ABSTRACT_V26.md"
]
for f in html_files:
    patch_file(f, html_repl)

# careful files
qna_repl = html_repl.copy()
# Remove generic replacements that might break Litvinukova citation if we added any
patch_file("scientific_qna.html", qna_repl)
patch_file("ZENITH_FOUNDATION_MODEL_CARD.md", qna_repl)

# Make sure profile.html has its v28_clinical_report.html link fixed, just in case
replace_in_file("profile.html", "v28_clinical_report.html", "v29_clinical_report.html")

print("Done patching files.")
