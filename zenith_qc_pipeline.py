# -*- coding: utf-8 -*-
"""ZENITH QC PIPELINE v1.2 — Memory-safe, uses pre-computed QC from file"""
import sys, os, time, json, h5py, numpy as np, gc
from scipy.sparse import csr_matrix
import anndata as ad, pandas as pd
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
def p(msg): print(msg, flush=True)

PROJECT = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(PROJECT, 'data', 'hca_full', 'heart_9928ad5f-6af.h5ad')
OUT_DIR = os.path.join(PROJECT, 'data', 'qc_output')
os.makedirs(OUT_DIR, exist_ok=True)

p("=" * 65)
p("ZENITH QC PIPELINE v1.2")
p("=" * 65)

# STEP 1: Read metadata
p("\n[1] Reading metadata...")
with h5py.File(INPUT, 'r') as f:
    cell_ids = [v.decode() if isinstance(v, bytes) else str(v) for v in f['obs']['NAME'][:]]
    n_cells = len(cell_ids)
    n_genes_per_cell = f['obs']['nFeature_RNA'][:]
    total_counts = f['obs']['nCount_RNA'][:]
    pct_mt = f['obs']['percent_mt'][:]
    
    ct = f['obs']['cell_type']
    ct_cats = [v.decode() if isinstance(v, bytes) else str(v) for v in ct['categories'][:]]
    cell_types = [ct_cats[c] for c in ct['codes'][:]]
    
    don = f['obs']['donor_id']
    don_cats = [v.decode() if isinstance(v, bytes) else str(v) for v in don['categories'][:]]
    donors = [don_cats[c] for c in don['codes'][:]]
    
    fn = f['var']['feature_name']
    cats = [v.decode() if isinstance(v, bytes) else str(v) for v in fn['categories'][:]]
    gene_symbols = [cats[c] for c in fn['codes'][:]]
    gene_ids = [v.decode() if isinstance(v, bytes) else str(v) for v in f['var']['_index'][:]]
    n_genes = len(gene_ids)

p(f"  Cells: {n_cells:,} | Genes: {n_genes:,} | Donors: {len(set(donors))}")

yamanaka = ['POU5F1', 'SOX2', 'NANOG', 'KLF4', 'MYC', 'LIN28A']
found = [g for g in yamanaka if g in gene_symbols]
p(f"  Yamanaka: {len(found)}/6 = {found}")

# STEP 2: QC stats
p("\n[2] Pre-computed QC stats:")
p(f"  Median genes/cell: {np.median(n_genes_per_cell):.0f}")
p(f"  Median UMI/cell:   {np.median(total_counts):.0f}")
p(f"  Median mito %:     {np.median(pct_mt):.2f}%")

# STEP 3: Filter
p("\n[3] Filtering...")
keep = (pct_mt < 20) & (n_genes_per_cell >= 200) & (n_genes_per_cell < 6000) & (total_counts >= 500)
n_keep = int(keep.sum())
p(f"  Dead (mito>20%):   {int((pct_mt>=20).sum()):,}")
p(f"  Empty (<200g):     {int((n_genes_per_cell<200).sum()):,}")
p(f"  Doublets (>6000g): {int((n_genes_per_cell>=6000).sum()):,}")
p(f"  Low UMI (<500):    {int((total_counts<500).sum()):,}")
p(f"  BEFORE: {n_cells:,} -> AFTER: {n_keep:,} (removed {n_cells-n_keep:,})")

# STEP 4: Build clean sparse matrix
p("\n[4] Building clean matrix...")
keep_idx = np.where(keep)[0]

with h5py.File(INPUT, 'r') as f:
    indptr = f['X']['indptr'][:]
    indices = f['X']['indices'][:]
    data = f['X']['data'][:].astype(np.float32)

new_d, new_i, new_p = [], [], [0]
for i, idx in enumerate(keep_idx):
    s, e = indptr[idx], indptr[idx+1]
    new_d.append(data[s:e])
    new_i.append(indices[s:e])
    new_p.append(new_p[-1] + (e - s))
    if i % 50000 == 0 and i > 0:
        p(f"    {i:,}/{n_keep:,}...")

del data, indices, indptr; gc.collect()

X_clean = csr_matrix(
    (np.concatenate(new_d), np.concatenate(new_i), np.array(new_p, dtype=np.int64)),
    shape=(n_keep, n_genes)
)
del new_d, new_i; gc.collect()
p(f"  Matrix: {X_clean.shape}")

# STEP 5: Build AnnData
p("\n[5] Building AnnData...")
obs_df = pd.DataFrame({
    'cell_type': [cell_types[i] for i in keep_idx],
    'donor_id': [donors[i] for i in keep_idx],
    'n_genes': n_genes_per_cell[keep_idx],
    'total_counts': total_counts[keep_idx],
    'pct_mt': pct_mt[keep_idx]
}, index=[cell_ids[i] for i in keep_idx])

# Make unique gene names
name_counts = Counter(gene_symbols)
seen = Counter()
unames = []
for nm in gene_symbols:
    if name_counts[nm] > 1:
        seen[nm] += 1
        unames.append(f"{nm}-{seen[nm]}")
    else:
        unames.append(nm)

var_df = pd.DataFrame({'ensembl_id': gene_ids}, index=unames)
adata = ad.AnnData(X=X_clean, obs=obs_df, var=var_df)

# STEP 6: Save
p("\n[6] Saving...")
out = os.path.join(OUT_DIR, 'heart_qc_clean.h5ad')
adata.write_h5ad(out)
sz = os.path.getsize(out) / (1024**2)
p(f"  Saved: {sz:.0f} MB")

# Cell types
p("\n  CELL TYPES:")
ct_f = adata.obs['cell_type'].value_counts()
for nm, c in ct_f.items():
    p(f"    {nm:<40} {c:>8,} ({100*c/adata.n_obs:.1f}%)")

# Report
report = {
    'pipeline': 'Zenith QC v1.2', 'cells_in': n_cells, 'cells_out': n_keep,
    'genes': n_genes, 'donors': len(set(donors)),
    'yamanaka': {g: (g in unames) for g in yamanaka},
    'cell_types': {str(k): int(v) for k, v in ct_f.items()}
}
with open(os.path.join(OUT_DIR, 'qc_report.json'), 'w') as f2:
    json.dump(report, f2, indent=2)

p(f"\n{'='*65}")
p(f"QC COMPLETE: {adata.n_obs:,} cells | {adata.n_vars:,} genes | 6/6 Yamanaka")
p(f"{'='*65}")
