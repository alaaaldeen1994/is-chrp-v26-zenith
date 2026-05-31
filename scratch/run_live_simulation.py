import sys
import os
import json
import warnings
warnings.simplefilter("ignore")

# Add project root to path
sys.path.append(os.getcwd())

from perturbation_engine import PerturbationEngine

def run_simulation(model_name, model_dir):
    print(f"\n" + "="*70)
    print(f" SIMULATING REPROGRAMMING ON MODEL: {model_name}")
    print(f" Path: {model_dir}")
    print("="*70)
    
    # Initialize the PerturbationEngine with this model
    engine = PerturbationEngine(model_dir=model_dir)
    engine.initialize()
    
    if engine.mode == "fallback":
        print("  [Warning] Engine initialized in fallback mode.")
        return
        
    print(f"  [OK] Manifold active: {len(engine.var_names):,} genes loaded.")
    
    # Define test cocktails
    gmt_cocktail = ["GATA4", "MEF2C", "TBX5"]
    zenith_cocktail = ["GATA4", "MEF2C", "TBX5", "SOX2"]
    
    # 1. Simulate GMT (Classic Cardiac Reprogramming)
    print("\n  [Cocktail 1] GMT (GATA4 + MEF2C + TBX5) - Classic 3-Factor")
    res_gmt = engine.predict_factor_effect(gmt_cocktail, source_type="Fibroblast", target_type="Cardiomyocyte", dose=1.0)
    print(f"    - Status:             {res_gmt['status']}")
    print(f"    - Latent Displacement: {res_gmt['latent_displacement']}")
    print(f"    - Nearest Phenotype:  {res_gmt['nearest_type']} (distance: {res_gmt['distance_to_nearest']})")
    print(f"    - Upregulated Genes:  {res_gmt['deg_up'][:8]}")
    
    # 2. Simulate Zenith v28 (4-Factor Hybrid Discovery)
    print("\n  [Cocktail 2] Zenith-4 (GATA4 + MEF2C + TBX5 + SOX2) - Upgraded 4-Factor")
    res_zenith = engine.predict_factor_effect(zenith_cocktail, source_type="Fibroblast", target_type="Cardiomyocyte", dose=1.0)
    print(f"    - Status:             {res_zenith['status']}")
    print(f"    - Latent Displacement: {res_zenith['latent_displacement']}")
    print(f"    - Nearest Phenotype:  {res_zenith['nearest_type']} (distance: {res_zenith['distance_to_nearest']})")
    print(f"    - Upregulated Genes:  {res_zenith['deg_up'][:8]}")
    
    # 3. Trajectory optimal transport simulation (GMT vs Zenith)
    print("\n  [Trajectory] Simulating transition trajectory (20 steps)...")
    traj = engine.predict_trajectory(source_type="Fibroblast", target_type="Cardiomyocyte", n_steps=5, genes_of_interest=["TNNT2", "TTN", "MYH7"])
    print(f"    - Step count: {traj['steps']}")
    for g, vals in traj['expression'].items():
        formatted_vals = ", ".join([f"{v:.4f}" for v in vals])
        print(f"    - {g:6} Expression Timeline: [{formatted_vals}]")

if __name__ == "__main__":
    project_root = os.getcwd()
    
    # Run simulation on restored HCA baseline model
    hca_dir = os.path.join(project_root, "models", "scvi_model_hca")
    run_simulation("HCA Heart Baseline (26.6K Genes)", hca_dir)
    
    # Run simulation on Zenith production model
    zenith_dir = os.path.join(project_root, "models", "zenith_foundation_v1")
    run_simulation("Zenith v28.0 Production (4.9K Genes)", zenith_dir)
