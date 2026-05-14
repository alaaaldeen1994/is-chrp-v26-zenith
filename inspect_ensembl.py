# -*- coding: utf-8 -*-
"""
Ensembl â†’ Gene Symbol Mapping for the 486k Heart Cell Atlas
Step 1: Check what gene metadata exists in the file
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
def p(msg): print(msg, flush=True)

import h5py

# Use h5py to read metadata WITHOUT loading the full 3GB into RAM
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                    "data", "hca_full", "heart_adult_full.h5ad")

p("=" * 60)
p("ENSEMBL MAPPING - Step 1: Inspect Gene Metadata")
p(f"File: {os.path.basename(FILE)}")
p("=" * 60)

with h5py.File(FILE, 'r') as f:
    p(f"\nTop-level keys: {list(f.keys())}")
    
    # Check var (gene metadata)
    if 'var' in f:
        var = f['var']
        p(f"\nGene metadata columns: {list(var.keys())}")
        
        # Check each column for gene symbols
        for col in var.keys():
            data = var[col]
            if hasattr(data, 'shape'):
                p(f"\n  Column '{col}':")
                p(f"    Shape: {data.shape}")
                p(f"    Dtype: {data.dtype}")
                
                # Show first 5 values
                try:
                    vals = data[:5]
                    if data.dtype.kind == 'O' or data.dtype.kind == 'S':
                        vals = [v.decode('utf-8') if isinstance(v, bytes) else str(v) for v in vals]
                    p(f"    First 5: {vals}")
                    
                    # Check if this column has POU5F1 or known gene symbols
                    all_vals = data[:]
                    if data.dtype.kind == 'O' or data.dtype.kind == 'S':
                        all_vals = [v.decode('utf-8') if isinstance(v, bytes) else str(v) for v in all_vals]
                        
                        yamanaka = ['POU5F1', 'SOX2', 'NANOG', 'KLF4', 'MYC', 'LIN28A']
                        found = [g for g in yamanaka if g in all_vals]
                        if found:
                            p(f"    *** YAMANAKA FOUND HERE: {found} ***")
                        
                        # Check for ENSG pattern
                        ensg_count = sum(1 for v in all_vals[:100] if str(v).startswith('ENSG'))
                        if ensg_count > 0:
                            p(f"    Ensembl IDs: {ensg_count}/100 first entries")
                except Exception as e:
                    p(f"    Error reading: {e}")
    
    # Also check if gene names are in the index
    if 'var' in f and '__categories' in f['var']:
        p(f"\n  Categories: {list(f['var']['__categories'].keys())}")
        for cat in f['var']['__categories'].keys():
            data = f['var']['__categories'][cat]
            vals = data[:5]
            vals = [v.decode('utf-8') if isinstance(v, bytes) else str(v) for v in vals]
            p(f"    {cat} (first 5): {vals}")
            
            yamanaka = ['POU5F1', 'SOX2', 'NANOG', 'KLF4', 'MYC', 'LIN28A']
            all_vals = [v.decode('utf-8') if isinstance(v, bytes) else str(v) for v in data[:]]
            found = [g for g in yamanaka if g in all_vals]
            if found:
                p(f"    *** YAMANAKA FOUND: {found} ***")

p("\nDone.")
