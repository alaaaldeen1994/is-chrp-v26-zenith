# ZENITH v27.0 GOLD â€” How to Deploy the 486k Model to Railway
# After Google Colab training finishes

# =====================================================================
# STEP 1: Download model from Google Drive
# =====================================================================
# Go to: https://drive.google.com/drive/folders/... (your Zenith_Data folder)
# You will see a NEW folder: "zenith_v26_486k_model"
# Right-click â†’ Download (it will zip it)
# Extract the zip on your PC

# =====================================================================
# STEP 2: Place the model in the correct folder
# =====================================================================
# The extracted folder contains: model.pt, model_params.pt, adata.h5ad, etc.
# Copy/move it here:
#   c:\Users\tariq\.gemini\antigravity\scratch\is-chrp-v26-generative\models\scvi_model_486k\
#
# It should look like:
#   models/
#     scvi_model_486k/
#       model.pt         <-- The trained weights
#       model_params.pt  <-- Model parameters
#       adata.h5ad       <-- The reference AnnData

# =====================================================================
# STEP 3: Verify the model loads correctly (run this script)
# =====================================================================
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "models", "scvi_model_486k")

if not os.path.exists(MODEL_PATH):
    print("ERROR: Model folder not found at:", MODEL_PATH)
    print("Please complete Step 2 above first.")
else:
    print("Model folder found:", MODEL_PATH)
    files = os.listdir(MODEL_PATH)
    print("Files:", files)
    
    try:
        import anndata as ad
        from scvi.model import SCVI
        
        print("Loading scVI model directly (no adata required for v1.0+)...")
        model = SCVI.load(MODEL_PATH)
        print("SUCCESS: 486k model verified and ready!")
        
        # Check Yamanaka factors if var_names are present in the model
        if hasattr(model, "var_names") and model.var_names is not None:
            yamanaka = ['POU5F1', 'SOX2', 'NANOG', 'KLF4', 'MYC', 'LIN28A']
            found = [g for g in yamanaka if g in model.var_names]
            print(f"Yamanaka factors: {len(found)}/6 = {found}")
            
    except Exception as e:
        print(f"Error loading model: {e}")

# =====================================================================
# STEP 4: Push to GitHub (Railway will auto-deploy)
# =====================================================================
# The model files are in .gitignore so they won't be committed.
# But bridge_server.py IS committed and already has the 486k support.
# Railway uses the models/ folder from its own persistent storage.
#
# To update Railway:
#   git add bridge_server.py
#   git commit -m "feat: Add 486k scVI model priority loading (Zenith v27.0 GOLD)"
#   git push
