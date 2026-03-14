# scVI Model Directory

Place your pre-trained **scVI-tools** model folder here.

### Requirements:
1. The folder name must be `scvi_model`.
2. It should contain the standard scVI save files:
   - `model.pt`
   - `attr.pkl`
   - `var_names.csv` (optional but recommended)

### How to save a model for this bridge:
In your Jupyter Notebook or Python script, run:
```python
model.save("models/scvi_model", overwrite=True)
```

### Gene Alignment:
The bridge assumes your simulation genes are mapped to the following symbols in your training data:
1. OCT4 -> `POU5F1`
2. NEURO -> `NEUROD1`
3. CARDIO -> `NKX2-5`
4. MYC -> `MYC`
5. SOX2 -> `SOX2`
6. KLF4 -> `KLF4`
7. NANOG -> `NANOG`
8. P53 -> `TP53`
9. GATA4 -> `GATA4`
10. PAX6 -> `PAX6`
11. BRACH -> `TBX5`
12. CHROM -> `CHRNA1`
