
import sys
try:
    import scanpy as sc
    print("SCANPY: OK")
except ImportError:
    print("SCANPY: MISSING")

try:
    import scvi
    print("SCVI: OK")
except ImportError:
    print("SCVI: MISSING")
