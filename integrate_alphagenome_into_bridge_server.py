import os, subprocess

base = r'C:\Users\alaaa\.gemini\antigravity\scratch\is-chrp-v26-generative'
server_path = os.path.join(base, 'bridge_server.py')

with open(server_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Import AlphaGenomeEngine if not already imported
if "from services.alphagenome_engine import AlphaGenomeEngine" not in content:
    content = "from services.alphagenome_engine import AlphaGenomeEngine\n" + content

# Replace simplified route with rich engine call
old_route = """@app.post("/api/v2/alphagenome/variant-audit")
async def run_alphagenome_variant_audit(req: AlphaGenomeRequest):
    var_str = req.variant or "chr12:111,842,901 C>T"
    gene = req.gene_target or "MYH6"
    disease = req.disease_context or "Cardiomyopathy"
    
    # Calculate non-coding pathogenicity prediction via long-range genomic model
    alphagenome_score = 0.942  # High confidence pathogenic prediction in 98% non-coding genome
    
    return {
        "status": "SUCCESS",
        "variant": var_str,
        "region_type": "98% Non-Coding Enhancer Element (Active Chromatin Domain)",
        "alphagenome_score": alphagenome_score,
        "pathogenicity_label": "PATHOGENIC NON-CODING VARIANT",
        "chromatin_accessibility_delta": "-68.4% ATAC-seq Signal Reduction",
        "tf_motif_disruption": f"Disrupts pioneer TF binding motif for {gene} co-regulation",
        "multigenic_cascade": {
            "primary_impacted_genes": [gene, "TNNT2", "GATA4", "MEF2C"],
            "epistatic_drift_index": 0.418,
            "grn_network_perturbation": "Cascade triggers down-regulation of structural cardiac sarcomere GRN."
        },
        "crispr_correction_strategy": {
            "editor_type": "Adenine Base Editor (ABE8e) / Prime Editor 2",
            "sgRNA_sequence": "5'- CCTGTGACTGTGGGGTTCA -3'",
            "pam_site": "5'- NGG -3' (Position +5 in protospacer window)",
            "correction_target": f"{var_str} -> Restored to Wild-Type Reference Sequence",
            "predicted_rejuvenation_recovery": "+38.5% Horvath Epigenetic Stability Recovery"
        },
        "scientific_rationale": f"AlphaGenome long-range genomic model analyzed 100kb context around {var_str}. Identified critical non-coding enhancer element driving {gene} expression in 98% dark genome. Precision ABE8e base editor sgRNA generated for targeted CRISPR correction."
    }"""

new_route = """@app.post("/api/v2/alphagenome/variant-audit")
async def run_alphagenome_variant_audit(req: AlphaGenomeRequest):
    var_str = req.variant or "chr12:111,842,901 C>T"
    gene = req.gene_target or "MYH6"
    disease = req.disease_context or "Cardiomyopathy"
    return AlphaGenomeEngine.audit_variant(var_str, gene, disease)

@app.get("/api/v2/alphagenome/presets")
async def get_alphagenome_presets():
    return {
        "status": "SUCCESS",
        "preset_variants": list(AlphaGenomeEngine.PRESET_VARIANTS.keys()),
        "descriptions": AlphaGenomeEngine.PRESET_VARIANTS
    }"""

if old_route in content:
    content = content.replace(old_route, new_route)
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Updated bridge_server.py with AlphaGenomeEngine calls!")
else:
    print("WARNING: old_route not matched in bridge_server.py")

res = subprocess.run(['python', '-c', 'import bridge_server; print("bridge_server imported successfully!")'], capture_output=True, text=True, cwd=base)
print("bridge_server test output:")
print(res.stdout)
if res.returncode != 0:
    print("Stderr:", res.stderr)
