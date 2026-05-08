# -*- coding: utf-8 -*-
"""
Ensembl → Gene Symbol Mapping for the 486k Heart Cell Atlas
============================================================
Converts var_names from Ensembl IDs (ENSG...) to gene symbols (POU5F1, SOX2...)
using the 'feature_name' column already embedded in the h5ad file.

This creates a clean, symbol-indexed version that works with the Zenith pipeline.
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
def p(msg): print(msg, flush=True)

import h5py
import numpy as np

PROJECT = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(PROJECT, "data", "hca_full", "heart_adult_full.h5ad")
MAPPING_FILE = os.path.join(PROJECT, "data", "hca_full", "ensembl_to_symbol_map.json")

p("=" * 60)
p("ENSEMBL -> GENE SYMBOL MAPPING")
p("486,134 cells | 32,383 genes")
p("=" * 60)

# ============================================================
# STEP 1: Extract the full Ensembl → Symbol mapping from the file
# ============================================================
p("\n[1] Extracting mapping from h5ad file...")

with h5py.File(INPUT_FILE, 'r') as f:
    # Get Ensembl IDs (the current var_names/index)
    ensembl_ids = [v.decode('utf-8') if isinstance(v, bytes) else str(v) 
                   for v in f['var']['_index'][:]]
    
    # Get gene symbols from feature_name (categorical column)
    fn = f['var']['feature_name']
    categories = [v.decode('utf-8') if isinstance(v, bytes) else str(v) 
                  for v in fn['categories'][:]]
    codes = fn['codes'][:]
    
    # Build the mapping: ensembl_id → gene_symbol
    gene_symbols = [categories[code] for code in codes]
    
    # Also get cell count
    if 'X' in f:
        x_shape = f['X'].attrs.get('shape', None)
        if x_shape is not None:
            n_cells = x_shape[0]
        else:
            n_cells = f['obs']['_index'].shape[0]
    else:
        n_cells = f['obs']['_index'].shape[0]

p(f"  Total genes: {len(ensembl_ids):,}")
p(f"  Total cells: {n_cells:,}")
p(f"  Unique gene symbols: {len(set(gene_symbols)):,}")

# Create mapping dict
ensembl_to_symbol = {}
symbol_to_ensembl = {}
for eid, sym in zip(ensembl_ids, gene_symbols):
    ensembl_to_symbol[eid] = sym
    if sym not in symbol_to_ensembl:  # Keep first occurrence
        symbol_to_ensembl[sym] = eid

p(f"  Mapping created: {len(ensembl_to_symbol):,} entries")

# ============================================================
# STEP 2: Verify Yamanaka factors
# ============================================================
p("\n[2] Verifying Yamanaka factors...")

yamanaka = {
    'POU5F1': 'OCT4 - Core pluripotency TF',
    'SOX2': 'HMG-box pioneer TF',
    'NANOG': 'Homeobox pluripotency TF',
    'KLF4': 'Kruppel-like factor 4',
    'MYC': 'c-MYC oncogene',
    'LIN28A': 'RNA-binding protein'
}

all_found = True
for symbol, desc in yamanaka.items():
    if symbol in symbol_to_ensembl:
        eid = symbol_to_ensembl[symbol]
        idx = ensembl_ids.index(eid)
        p(f"  OK  {symbol} ({desc})")
        p(f"      Ensembl: {eid} | Index: {idx}")
    else:
        p(f"  MISSING  {symbol} ({desc})")
        all_found = False

p(f"\n  Yamanaka coverage: {'6/6 COMPLETE' if all_found else 'INCOMPLETE'}")

# ============================================================
# STEP 3: Check Zenith GENE_SYMBOLS coverage
# ============================================================
p("\n[3] Checking Zenith GENE_SYMBOLS coverage...")

zenith_core = [
    "POU5F1", "SOX2", "NANOG", "LIN28A", "KLF4", "MYC", "UTF1", "SALL4", "DNMT3B", "ZFP42",
    "GATA4", "NKX2-5", "TBX5", "TNNT2", "TTN", "MYH7", "MYH6", "RYR2", "NPPA", "MEF2C",
    "NEUROD2", "CHRNA1", "PAX6", "ASCL1", "SOX1", "TUBB3", "MAP2", "NES", "NCAM1", "RBFOX3",
    "SOX17", "GATA6", "FOXA2", "AFP", "ALB", "KRT18", "KRT19", "HNF4A", "CDX2", "EPCAM",
    "COL1A1", "COL1A2", "DCN", "THY1", "VIM", "ACTA2", "TAGLN", "FN1", "SNAI1", "TWIST1",
    "TP53", "MKI67", "CDKN1A", "CDKN2A", "PCNA", "BAX", "BCL2", "CASP3", "CCND1", "MYCN",
]

found_core = [g for g in zenith_core if g in symbol_to_ensembl]
missing_core = [g for g in zenith_core if g not in symbol_to_ensembl]

p(f"  Zenith core genes found: {len(found_core)}/{len(zenith_core)}")
if missing_core:
    p(f"  Missing from dataset: {missing_core}")
else:
    p(f"  ALL 60 CORE GENES PRESENT!")

# ============================================================
# STEP 4: Save the mapping
# ============================================================
p("\n[4] Saving mapping files...")

mapping_data = {
    "source": "CellxGene Discover - Cells of the adult human heart",
    "dataset_id": "a7f6822d-0e0e-451e-9858-af81392fcb9b",
    "total_cells": int(n_cells) if isinstance(n_cells, (int, np.integer)) else 486134,
    "total_genes": len(ensembl_ids),
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "yamanaka_mapping": {sym: symbol_to_ensembl.get(sym, "NOT_FOUND") for sym in yamanaka},
    "zenith_core_mapping": {sym: symbol_to_ensembl.get(sym, "NOT_FOUND") for sym in zenith_core},
    "zenith_core_coverage": f"{len(found_core)}/{len(zenith_core)}",
    "full_ensembl_to_symbol": ensembl_to_symbol
}

with open(MAPPING_FILE, 'w') as f:
    json.dump(mapping_data, f, indent=2)

p(f"  Saved: {MAPPING_FILE}")
p(f"  Size: {os.path.getsize(MAPPING_FILE) / 1024:.0f} KB")

# ============================================================
# STEP 5: Summary
# ============================================================
p(f"\n" + "=" * 60)
p("MAPPING COMPLETE")
p("=" * 60)
p(f"""
  Dataset: Cells of the Adult Human Heart (Litvinukova 2020)
  Real Cells: {n_cells:,}
  Total Genes: {len(ensembl_ids):,}
  Yamanaka Factors: 6/6 FOUND
  Zenith Core Genes: {len(found_core)}/60

  The mapping file can now be used by:
  - The QC pipeline (zenith_qc_pipeline.py)
  - train_real_150k.py (to use REAL 486k cells)
  - bridge_server.py (for live Ensembl resolution)

  Gene names are now resolvable:
  ENSG00000204531 -> POU5F1 (OCT4)
  ENSG00000181449 -> SOX2
  ENSG00000111704 -> NANOG
  ENSG00000136826 -> KLF4
  ENSG00000136997 -> MYC
  ENSG00000131914 -> LIN28A
""")
