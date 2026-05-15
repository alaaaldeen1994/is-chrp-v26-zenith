import os
import sys

# Path Integrity Test for Zenith v27.0 GOLD
def run_integrity_test():
    print("=" * 60)
    print("ZENITH PLATFORM: LOCAL PATH INTEGRITY TEST")
    print("=" * 60)

    # 1. Check Project Root
    project_root = os.getcwd()
    print(f"[1] Project Root: {project_root}")

    # 2. Check 486k Model Folder
    model_dir = os.path.join(project_root, "models", "scvi_model_hca")
    print(f"[2] Model Directory: {model_dir}")
    
    if os.path.exists(model_dir):
        print("    [OK] SUCCESS: Model directory found.")
    else:
        print("    [ERROR] ERROR: Model directory missing.")
        return

    # 3. Check Critical Model Files
    critical_files = ["model.pt", "adata.h5ad"]
    for f in critical_files:
        f_path = os.path.join(model_dir, f)
        if os.path.exists(f_path):
            size = os.path.getsize(f_path) / (1024*1024)
            print(f"    [OK] File '{f}' found ({size:.2f} MB)")
        else:
            print(f"    [ERROR] File '{f}' is missing from models folder.")

    # 4. Check Main HCA Full Dataset (Master)
    master_data = os.path.join(project_root, "data", "qc_output", "heart_qc_clean.h5ad")
    print(f"[3] Master Audit Dataset: {master_data}")
    if os.path.exists(master_data):
        size = os.path.getsize(master_data) / (1024*1024*1024)
        print(f"    [OK] SUCCESS: Master dataset found ({size:.2f} GB)")
    else:
        print("    [NOTICE] NOTICE: Master QC dataset not in local folder (Expected if stored only in Drive).")

    # 5. Verify Python Environment for scVI
    print("[4] Environment Verification:")
    try:
        import scvi
        import anndata
        print(f"    [OK] scvi-tools version: {scvi.__version__}")
        print(f"    [OK] anndata version:   {anndata.__version__}")
    except ImportError as e:
        print(f"    ❌ ERROR: Required libraries missing: {e}")

    print("\n" + "=" * 60)
    print("INTEGRITY TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_integrity_test()
