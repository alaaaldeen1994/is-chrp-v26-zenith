import os
import pickle
import urllib.parse
import urllib.request
import h5py
import numpy as np
import pandas as pd
from scipy import stats

LIT_PATH = "data/foundation/raw_datasets/d4e69e01-3ba2-4d6b-a15d-e7048f78f22e.h5ad"
PERI_PATH = "data/foundation/raw_datasets/f1606894-59df-4794-a37f-baa7c6fb6de1.h5ad"
CACHE_PATH = "scratch/phaseE_pseudobulk_cache.pkl"
BIOMART_CACHE = "scratch/grch38_gene_annotations.tsv"

LIT_AGE_MAP = {
    "D1": 52.5, "D2": 62.5, "D3": 57.5, "D4": 72.5, "D5": 67.5, "D6": 72.5, "D7": 62.5,
    "D11": 62.5, "H2": 52.5, "H3": 52.5, "H4": 57.5, "H5": 52.5, "H6": 42.5, "H7": 47.5
}

PERI_STAGE_MAP = {
    "fifth decade stage": 45.0,
    "sixth decade stage": 55.0,
    "seventh decade stage": 65.0,
    "eighth decade stage": 75.0,
    "ninth decade stage": 85.0,
}


def decode_var_col(grp):
    if isinstance(grp, h5py.Group) and "categories" in grp:
        cats = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in grp["categories"][:]]
        codes = grp["codes"][:]
        return np.array([cats[c] if c >= 0 else "" for c in codes], dtype=object)
    vals = grp[:]
    return np.array([x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in vals], dtype=object)


def fetch_biomart():
    if os.path.exists(BIOMART_CACHE) and os.path.getsize(BIOMART_CACHE) > 100000:
        return pd.read_csv(BIOMART_CACHE, sep="\t", low_memory=False)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE Query>'
        '<Query virtualSchemaName="default" formatter="TSV" header="1" uniqueRows="1" count="" datasetConfigVersion="0.6">'
        '<Dataset name="hsapiens_gene_ensembl" interface="default">'
        '<Attribute name="ensembl_gene_id" />'
        '<Attribute name="start_position" />'
        '<Attribute name="end_position" />'
        '<Attribute name="gene_biotype" />'
        '<Attribute name="chromosome_name" />'
        '</Dataset>'
        '</Query>'
    )
    for host in ["https://www.ensembl.org", "http://www.ensembl.org", "https://useast.ensembl.org", "https://asia.ensembl.org"]:
        try:
            url = f"{host}/biomart/martservice?query=" + urllib.parse.quote(xml)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                txt = resp.read().decode("utf-8")
                if "ensembl_gene_id" in txt or "Gene stable ID" in txt:
                    with open(BIOMART_CACHE, "w", encoding="utf-8") as f:
                        f.write(txt)
                    print(f"[+] Downloaded BioMart GRCh38 annotations from {host}: {len(txt.splitlines())} rows")
                    return pd.read_csv(BIOMART_CACHE, sep="\t", low_memory=False)
        except Exception as e:
            print(f"[-] BioMart {host} error: {e}")
    return None


def compute_cohort_stats(pb_dict, age_map, expr_frac, min_detect=0.05):
    donors = sorted([d for d in pb_dict.keys() if d in age_map])
    ages = np.array([age_map[d] for d in donors], dtype=np.float64)
    youth = -ages
    mat = np.vstack([pb_dict[d][0] for d in donors])  # (n_donors, n_genes)
    mean_expr = mat.mean(axis=0)

    # Also compute Harvard (H*) vs Sanger (D*) difference if Litvinukova
    h_idx = [i for i, d in enumerate(donors) if d.startswith("H")]
    d_idx = [i for i, d in enumerate(donors) if d.startswith("D")]
    if h_idx and d_idx:
        harvard_minus_sanger = mat[h_idx].mean(axis=0) - mat[d_idx].mean(axis=0)
    else:
        harvard_minus_sanger = np.zeros_like(mean_expr)

    yc = youth - youth.mean()
    yn = np.sqrt(np.sum(yc ** 2))
    mc = mat - mat.mean(axis=0, keepdims=True)
    mn = np.sqrt(np.sum(mc ** 2, axis=0))
    valid = mn > 1e-12
    r_youth = np.zeros(mat.shape[1], dtype=np.float64)
    r_youth[valid] = (yc @ mc[:, valid]) / (yn * mn[valid])
    active_mask = (expr_frac >= min_detect) & valid
    return {
        "r_youth": r_youth,
        "mean_expr": mean_expr,
        "harvard_minus_sanger": harvard_minus_sanger,
        "active_mask": active_mask,
    }


def partial_corr(x, y, covars):
    """Computes Pearson partial correlation between x and y adjusting for columns in covars."""
    X = np.column_stack([np.ones(len(x)), covars])
    bx, _, _, _ = np.linalg.lstsq(X, x, rcond=None)
    by, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    rx = x - X @ bx
    ry = y - X @ by
    r, p = stats.pearsonr(rx, ry)
    conc = np.mean(np.sign(rx) == np.sign(ry)) * 100.0
    return r, p, conc


def main():
    with h5py.File(LIT_PATH, "r") as f:
        ens_ids = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in f["var"]["_index"][:]]
        feat_len_raw = decode_var_col(f["var"]["feature_length"]).astype(float)
        feat_type_raw = decode_var_col(f["var"]["feature_type"])
        feat_name_raw = decode_var_col(f["var"]["feature_name"])

    print("Unique feature_type values in h5ad var:", pd.Series(feat_type_raw).value_counts().to_dict())

    bm_df = fetch_biomart()
    span_map = {}
    biotype_map = {}
    chrom_map = {}
    if bm_df is not None:
        cols = bm_df.columns.tolist()
        c_id, c_s, c_e, c_b, c_ch = cols[0], cols[1], cols[2], cols[3], cols[4]
        for _, row in bm_df.iterrows():
            gid = str(row[c_id])
            try:
                span = abs(float(row[c_e]) - float(row[c_s])) + 1.0
                span_map[gid] = span
                biotype_map[gid] = str(row[c_b])
                chrom_map[gid] = str(row[c_ch])
            except Exception:
                pass

    with open(CACHE_PATH, "rb") as cf:
        lit_ens, lit_syms, lit_pb, lit_frac, peri_ens, peri_syms, peri_pb, peri_frac = pickle.load(cf)

    with h5py.File(PERI_PATH, "r") as f:
        p_donors = decode_var_col(f["obs"]["donor_id"])
        p_stages = decode_var_col(f["obs"]["development_stage"])
    peri_age_map = {}
    for d, st in zip(p_donors, p_stages):
        if d not in peri_age_map and st in PERI_STAGE_MAP:
            peri_age_map[d] = PERI_STAGE_MAP[st]

    lit_fib = compute_cohort_stats(lit_pb["fibroblast"], LIT_AGE_MAP, lit_frac["fibroblast"])
    peri_fib = compute_cohort_stats(peri_pb["fibroblast"], peri_age_map, peri_frac["fibroblast"])

    lit_acm = compute_cohort_stats(lit_pb["regular atrial cardiac myocyte"], LIT_AGE_MAP, lit_frac["regular atrial cardiac myocyte"])
    peri_acm = compute_cohort_stats(peri_pb["cardiac muscle cell"], peri_age_map, peri_frac["cardiac muscle cell"])

    lit_idx_map = {e: i for i, e in enumerate(lit_ens)}
    peri_idx_map = {e: i for i, e in enumerate(peri_ens)}
    shared_ens = [e for e in lit_ens if e in peri_idx_map]

    for label, c1, c2 in [("Fibroblast (n=5,262)", lit_fib, peri_fib), ("Atrial CM Chamber-Matched (n=6,768)", lit_acm, peri_acm)]:
        print("\n" + "=" * 85)
        print(f"PART 3 GENE-PROPERTY ANALYSIS: {label}")
        print("=" * 85)
        rows = []
        for e in shared_ens:
            i1 = lit_idx_map[e]
            i2 = peri_idx_map[e]
            if not (c1["active_mask"][i1] and c2["active_mask"][i2]):
                continue
            sym = str(feat_name_raw[i1])
            exonic_len = float(feat_len_raw[i1])
            genomic_span = float(span_map.get(e, exonic_len))
            if genomic_span < exonic_len:
                genomic_span = exonic_len
            intron_len = max(0.0, genomic_span - exonic_len)
            intron_frac = intron_len / genomic_span if genomic_span > 0 else 0.0

            bt_raw = biotype_map.get(e, str(feat_type_raw[i1]))
            ch_raw = chrom_map.get(e, "")
            if sym.startswith("MT-") or ch_raw == "MT" or "Mt_" in bt_raw:
                biotype = "mitochondrial"
            elif "lncRNA" in bt_raw or "lincRNA" in bt_raw or "antisense" in bt_raw or sym.endswith("-AS1") or sym.startswith("LINC"):
                biotype = "lncRNA"
            elif "protein_coding" in bt_raw:
                biotype = "protein_coding"
            else:
                biotype = "other"

            rows.append({
                "ensembl_id": e,
                "symbol": sym,
                "r_lit": float(c1["r_youth"][i1]),
                "r_peri": float(c2["r_youth"][i2]),
                "mean_lit": float(c1["mean_expr"][i1]),
                "mean_peri": float(c2["mean_expr"][i2]),
                "h_minus_d": float(c1["harvard_minus_sanger"][i1]),
                "exonic_len": exonic_len,
                "genomic_span": genomic_span,
                "intron_len": intron_len,
                "intron_frac": intron_frac,
                "log10_span": np.log10(max(1.0, genomic_span)),
                "log10_intron": np.log10(intron_len + 1.0),
                "log10_exonic": np.log10(max(1.0, exonic_len)),
                "biotype": biotype,
                "is_lncRNA": 1.0 if biotype == "lncRNA" else 0.0,
                "is_mito": 1.0 if biotype == "mitochondrial" else 0.0,
                "is_pc": 1.0 if biotype == "protein_coding" else 0.0,
            })

        df = pd.DataFrame(rows)
        print(f"Total shared active genes analyzed: {len(df)} (BioMart span matched: {sum(df['ensembl_id'].isin(span_map))})")
        print("Biotype counts:", df["biotype"].value_counts().to_dict())

        print("\n--- 1 & 2. CORRELATIONS OF r_youth WITH GENE PROPERTIES ---")
        props = [
            ("log10(Genomic Span)", "log10_span"),
            ("log10(Total Intron Length + 1)", "log10_intron"),
            ("Intron Fraction (intron/span)", "intron_frac"),
            ("log10(Exonic Feature Length)", "log10_exonic"),
            ("Biotype: lncRNA (0/1)", "is_lncRNA"),
            ("Biotype: Mitochondrial (0/1)", "is_mito"),
            ("Biotype: Protein-Coding (0/1)", "is_pc"),
            ("Mean Expression in Litvinukova", "mean_lit"),
            ("Mean Expression in PERIHEART", "mean_peri"),
            ("Diff Mean Expr (Lit - Peri)", None),
            ("Within-Lit Harvard(Nuclei) - Sanger(Cells)", "h_minus_d"),
        ]
        df["diff_mean"] = df["mean_lit"] - df["mean_peri"]
        for pname, col in props:
            cname = col if col else "diff_mean"
            rl, pl = stats.pearsonr(df["r_lit"], df[cname])
            rp, pp = stats.pearsonr(df["r_peri"], df[cname])
            r_p12, _ = stats.pearsonr(df[cname], df["r_peri"])
            print(f"  {pname:<42} | Lit r={rl:+.4f} (p={pl:.2e}) | Peri r={rp:+.4f} (p={pp:.2e})")

        print("\n--- 3. MEAN r_youth IN EACH COHORT SPLIT BY BIOTYPE ---")
        for bt in ["protein_coding", "lncRNA", "mitochondrial", "other"]:
            sub = df[df["biotype"] == bt]
            if len(sub) > 0:
                print(f"  {bt:<16} (n={len(sub):4d}): Lit mean r_youth = {sub['r_lit'].mean():+.4f} (median {sub['r_lit'].median():+.4f}, %pos={(sub['r_lit']>0).mean()*100:.1f}%) | "
                      f"Peri mean r_youth = {sub['r_peri'].mean():+.4f} (median {sub['r_peri'].median():+.4f}, %pos={(sub['r_peri']>0).mean()*100:.1f}%)")

        print("\n--- 4. STRATIFIED CROSS-COHORT CORRELATION r(Lit r_youth, Peri r_youth) ---")
        for bt in ["protein_coding", "lncRNA", "mitochondrial", "other"]:
            sub = df[df["biotype"] == bt]
            if len(sub) >= 5:
                sr, sp = stats.pearsonr(sub["r_lit"], sub["r_peri"])
                print(f"  Biotype {bt:<15} (n={len(sub):4d}): r = {sr:+.4f} (p={sp:.2e})")

        df["span_q"] = pd.qcut(df["log10_span"], 4, labels=["Q1 (Shortest)", "Q2", "Q3", "Q4 (Longest)"])
        for q in ["Q1 (Shortest)", "Q2", "Q3", "Q4 (Longest)"]:
            sub = df[df["span_q"] == q]
            sr, sp = stats.pearsonr(sub["r_lit"], sub["r_peri"])
            print(f"  Gene Length {q:<15} (n={len(sub):4d}): r = {sr:+.4f} (p={sp:.2e}) | mean Lit r={sub['r_lit'].mean():+.4f}, mean Peri r={sub['r_peri'].mean():+.4f}")

        df["expr_q"] = pd.qcut(df["mean_lit"], 4, labels=["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"])
        for q in ["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"]:
            sub = df[df["expr_q"] == q]
            sr, sp = stats.pearsonr(sub["r_lit"], sub["r_peri"])
            print(f"  Lit Mean Expr {q:<13} (n={len(sub):4d}): r = {sr:+.4f} (p={sp:.2e}) | mean Lit r={sub['r_lit'].mean():+.4f}, mean Peri r={sub['r_peri'].mean():+.4f}")

        print("\n--- 5. PARTIAL CORRELATIONS r(Lit r_youth, Peri r_youth | covariates) ---")
        r_raw, p_raw = stats.pearsonr(df["r_lit"], df["r_peri"])
        print(f"  Unadjusted Raw Correlation                         : r = {r_raw:+.4f} (p={p_raw:.2e})")

        r_p1, p_p1, c_p1 = partial_corr(df["r_lit"].values, df["r_peri"].values, df[["log10_span", "log10_intron", "is_lncRNA", "is_mito"]].values)
        print(f"  Partial corr | Gene Length + Intron Len + Biotype  : r = {r_p1:+.4f} (p={p_p1:.2e}), sign_conc={c_p1:.2f}%")

        r_p2, p_p2, c_p2 = partial_corr(df["r_lit"].values, df["r_peri"].values, df[["log10_span", "log10_intron", "log10_exonic", "is_lncRNA", "is_mito", "mean_lit", "mean_peri"]].values)
        print(f"  Partial corr | Length + Biotype + Mean Expr (1&2)  : r = {r_p2:+.4f} (p={p_p2:.2e}), sign_conc={c_p2:.2f}%")

        r_p3, p_p3, c_p3 = partial_corr(df["r_lit"].values, df["r_peri"].values, df[["h_minus_d"]].values)
        print(f"  Partial corr | Harvard(Nuclei) - Sanger(Cells) diff: r = {r_p3:+.4f} (p={p_p3:.2e}), sign_conc={c_p3:.2f}%")


if __name__ == "__main__":
    main()
