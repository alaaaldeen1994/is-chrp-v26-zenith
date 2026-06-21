import os
import scvi

base_dir = os.path.abspath(os.path.dirname(__file__))
model_dir = os.path.join(base_dir, "models", "zenith_foundation_v1")

if os.path.exists(model_dir):
    try:
        model = scvi.model.SCVI.load(model_dir)
        print("Model loaded successfully!")
        print(f"Number of genes (var_names): {len(model.adata.var_names)}")
        print("First 10 genes:", list(model.adata.var_names[:10]))
        print("Last 10 genes:", list(model.adata.var_names[-10:]))
    except Exception as e:
        print(f"Error loading model: {e}")
else:
    print(f"Model directory not found at {model_dir}")
