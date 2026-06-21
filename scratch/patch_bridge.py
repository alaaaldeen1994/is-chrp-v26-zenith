"""
Patch bridge_server.py for v29.0 model:
  - 4908 genes → 5858 genes (tensor dimensions + comments)
  - 486k cells → 2M cells (comments/prints)
  - Update derived dimensions: 4909→5859, 9817→11717
  - Rename state_tensor_4908 → state_tensor_5858
"""

import os, sys

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bridge_server.py")
FILE = os.path.normpath(FILE)

print(f"Patching: {FILE}")

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

original = src  # keep copy for verification

# Ordered list of (old, new, expected_count_or_None) replacements.
# expected_count=None means "at least 1". An int means exactly that many.
replacements = [
    # 1. Line 780: input_dim default
    ("def __init__(self, input_dim=4908,", "def __init__(self, input_dim=5858,", 1),

    # 2. Line 860: Comment
    ("# Input format: [CurrentGenes(4908), TargetGenes(4908), BioAge(1)]",
     "# Input format: [CurrentGenes(5858), TargetGenes(5858), BioAge(1)]", 1),

    # 3. Line 1204: Comment (486k cells, 14 donors)
    ("486k cells, 14 donors", "2M cells, 83 donors", 1),

    # 4. Line 1207: Docstring
    ("Load exact 4908 var_names from scVI model schema",
     "Load exact 5858 var_names from scVI model schema", 1),

    # 5. Line 1392: Comment
    ("# Priority 1: 486k-cell model (trained on full Heart Cell Atlas)",
     "# Priority 1: 2M-cell model (trained on full Heart Cell Atlas)", 1),

    # 6. Line 1402: Comment
    ("# --- PRIORITY 1: REAL 486k Full HCA Model (Litvinukova et al. Nature 2020) ---",
     "# --- PRIORITY 1: REAL 2M Foundation Model (Litvinukova et al. Nature 2020) ---", 1),

    # 7. Line 1424: Print statement
    ('Detected 486k Full HCA Model', 'Detected 2M Foundation Model', 1),

    # 8. Line 1438: Warning print
    ('WARNING: 486k model found but failed to load',
     'WARNING: 2M model found but failed to load', 1),

    # 9. Line 1514: Note comment about 486k
    ("To upgrade, place 486k model", "To upgrade, place 2M model", 1),

    # 10. Line 1532: Fallback print about 486k
    ("place model in models/scvi_model_486k/", "place model in models/scvi_model_2M/", 1),

    # 11. Line 3333: Docstring
    ("exactly 4908) used in the v28 model", "exactly 5858) used in the v29 model", 1),

    # 12. Lines 3364, 3366, 3368: Reshape calls (3 occurrences)
    (".reshape(n_agents, 4908)", ".reshape(n_agents, 5858)", 3),

    # 13. Line 3414: context_tensor
    ("context_tensor = torch.zeros(n_agents, 4908)", "context_tensor = torch.zeros(n_agents, 5858)", 1),

    # 14. Line 3426: Comment
    ("# 3. Model Input Preparation (Strict 4908 Dimensions)",
     "# 3. Model Input Preparation (Strict 5858 Dimensions)", 1),

    # 15. Line 3428: Variable rename
    ("state_tensor_4908 = torch.tensor(genes_np, dtype=torch.float32)",
     "state_tensor_5858 = torch.tensor(genes_np, dtype=torch.float32)", 1),

    # 16. Line 3430: cat call + comment  (use the variable name too)
    ("torch.cat([state_tensor_4908, context_tensor, ages_tensor], dim=1) # [N, 9817]",
     "torch.cat([state_tensor_5858, context_tensor, ages_tensor], dim=1) # [N, 11717]", 1),

    # 17. Line 3444: Fallback drift zeros  (4909 = 4908+1 → 5859 = 5858+1)
    ("torch.zeros((n_agents, 4909), dtype=torch.float32)",
     "torch.zeros((n_agents, 5859), dtype=torch.float32)", 1),

    # 18. Line 3450: Comment
    ("# v28: VECTOR INJECTION (4908-dim)", "# v29: VECTOR INJECTION (5858-dim)", 1),

    # 19. Line 3456: np.zeros
    ("vec = np.zeros(4908)", "vec = np.zeros(5858)", 1),

    # 20. Line 3506: drift slice
    ("drift[:, :4908]", "drift[:, :5858]", 1),

    # 21. Line 3516: torch.zeros per-agent vector
    ("p_vec = torch.zeros(4908)", "p_vec = torch.zeros(5858)", 1),
]

for i, (old, new, expected) in enumerate(replacements, 1):
    count = src.count(old)
    if count == 0:
        print(f"  ERROR #{i}: Pattern not found: {old!r}")
        sys.exit(1)
    if expected is not None and count != expected:
        print(f"  ERROR #{i}: Expected {expected} occurrence(s) but found {count}: {old!r}")
        sys.exit(1)
    src = src.replace(old, new)
    print(f"  OK #{i}: Replaced {count}x: {old!r}")

# Verify we changed something
if src == original:
    print("ERROR: No changes were made!")
    sys.exit(1)

# Verify no stale 4908 remains in functional code (allow in unrelated comments/strings)
remaining = src.count("4908")
print(f"\n  Remaining occurrences of '4908' in file: {remaining}")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\nSUCCESS: Patched {FILE}")
print(f"  Total replacements applied: {len(replacements)}")
