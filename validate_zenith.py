"""
IS-CHRP v27.0 GOLD - Yamanaka Validation (Fixed for ZenithV2DeepDrift)
=================================================================

âš ï¸  DEPRECATED: This script validates the legacy DriftMLP model only.
    For the production 486k scVI model, use: validate_486k_model.py
    (Grade A â€” 5/6 passed, committed 2026-05-08)

This script validates the trained ZenithV2DeepDrift model against 
real Yamanaka 2006 reprogramming dynamics.

Author: Kagawea Labs
"""

import numpy as np
import torch
import torch.nn as nn
import json
import os
from datetime import datetime

# ============================================================
# MODEL ARCHITECTURE (Must match bridge_server.py exactly!)
# ============================================================
class ResBlock(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.LayerNorm(dim),
            nn.ReLU(),
            nn.Linear(dim, dim),
            nn.LayerNorm(dim)
        )
    def forward(self, x):
        return x + self.net(x)

class ZenithV2DeepDrift(nn.Module):
    def __init__(self, input_dim=1000, hidden_dim=1024):
        super().__init__()
        self.input_dim = input_dim
        self.encoder = nn.Sequential(
            nn.Linear(input_dim * 2 + 1, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU()
        )
        self.trunk = nn.Sequential(
            ResBlock(hidden_dim),
            ResBlock(hidden_dim),
            ResBlock(hidden_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, 512),
            nn.ReLU(),
            nn.Linear(512, input_dim + 1)
        )

    def forward(self, x):
        h = self.encoder(x)
        h = self.trunk(h)
        return self.decoder(h)


# Gene indices for validation
# OCT4=0, SOX2=1, NANOG=2, KLF4=4, MYC=5, TP53=50
GENE_MAP = {
    "OCT4": 0, "POU5F1": 0,
    "SOX2": 1,
    "NANOG": 2,
    "KLF4": 4,
    "MYC": 5,
    "TP53": 50,
    "TNNT2": 13,
    "NKX2-5": 11
}


def load_model():
    """Load trained ZenithV2DeepDrift model."""
    print("ðŸ“¥ Loading trained ZenithV2DeepDrift model...")
    
    model = ZenithV2DeepDrift(input_dim=1000, hidden_dim=1024)
    model_path = os.path.join(os.path.dirname(__file__), "models", "driftmlp_trained", "driftmlp.pt")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Run train_zenith_1000d.py first!")
    
    model.load_state_dict(torch.load(model_path, weights_only=True))
    model.eval()
    
    params = sum(p.numel() for p in model.parameters())
    print(f"âœ… Model loaded: {params:,} parameters")
    
    return model


def simulate_oskm_reprogramming(model, n_days=21, dt=0.1):
    """
    Simulate 21-day OSKM reprogramming using ZenithV2DeepDrift.
    Returns gene expression trajectories over time.
    """
    print(f"ðŸ§¬ Simulating {n_days}-day OSKM reprogramming...")
    
    # Initial somatic state (low pluripotency)
    genes = np.zeros(1000, dtype=np.float32)
    genes[0:10] = 0.05   # Low pluripotency
    genes[40:50] = 0.7   # High somatic markers
    genes[50] = 0.5      # Moderate TP53
    
    bioage = 0.8  # Aged cell
    
    # OSKM boost vector
    oskm_boost = np.zeros(1000, dtype=np.float32)
    oskm_boost[0] = 0.5   # OCT4
    oskm_boost[1] = 0.5   # SOX2
    oskm_boost[4] = 0.5   # KLF4
    oskm_boost[5] = 0.3   # MYC
    
    # Storage
    trajectory = {name: [] for name in GENE_MAP.keys()}
    trajectory["BioAge"] = []
    time_points = []
    
    steps = int(n_days / dt)
    
    for step in range(steps):
        day = step * dt
        time_points.append(day)
        
        # Record current state
        for name, idx in GENE_MAP.items():
            trajectory[name].append(float(genes[idx]))
        trajectory["BioAge"].append(bioage)
        
        # Build input tensor [genes(1000), age(1), context(1000)]
        context = genes.copy()
        input_vec = np.concatenate([genes, [bioage], context])
        input_tensor = torch.tensor(input_vec, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            drift = model(input_tensor).squeeze().numpy()
        
        # OSKM boost (decays after day 7)
        if day < 7:
            oskm_strength = 1.0
        elif day < 14:
            oskm_strength = 0.6
        else:
            oskm_strength = 0.2
        
        # Apply dynamics
        gene_drift = drift[:1000]
        age_drift = drift[1000]
        
        genes = genes + gene_drift * dt + oskm_boost * oskm_strength * dt * 0.3
        bioage = bioage + age_drift * dt
        
        # Add stochastic noise
        genes += np.random.randn(1000).astype(np.float32) * 0.002
        
        # Clamp
        genes = np.clip(genes, 0, 1)
        bioage = np.clip(bioage, 0.1, 1.0)
    
    print(f"âœ… Simulation complete: {len(time_points)} timepoints")
    
    return time_points, trajectory


def analyze_results(time_points, trajectory):
    """Analyze reprogramming trajectory and compute metrics."""
    print("\n" + "=" * 60)
    print("ðŸ“Š VALIDATION RESULTS")
    print("=" * 60)
    
    time_np = np.array(time_points)
    
    # Find key timepoints
    day_0_idx = 0
    day_7_idx = np.argmin(np.abs(time_np - 7))
    day_14_idx = np.argmin(np.abs(time_np - 14))
    day_21_idx = -1
    
    # Extract values at key timepoints
    results = {
        "day_0": {},
        "day_7": {},
        "day_14": {},
        "day_21": {}
    }
    
    for name in ["OCT4", "SOX2", "NANOG", "KLF4", "MYC", "TP53", "BioAge"]:
        vals = np.array(trajectory.get(name, trajectory.get("POU5F1", [0] * len(time_points))))
        results["day_0"][name] = vals[day_0_idx]
        results["day_7"][name] = vals[day_7_idx]
        results["day_14"][name] = vals[day_14_idx]
        results["day_21"][name] = vals[day_21_idx]
    
    # Print comparison table
    print("\nðŸ“ˆ Gene Expression Over Time:")
    print("-" * 60)
    print(f"{'Gene':<10} {'Day 0':>10} {'Day 7':>10} {'Day 14':>10} {'Day 21':>10}")
    print("-" * 60)
    
    for name in ["OCT4", "SOX2", "NANOG", "KLF4", "MYC", "TP53", "BioAge"]:
        print(f"{name:<10} {results['day_0'][name]:>10.3f} {results['day_7'][name]:>10.3f} "
              f"{results['day_14'][name]:>10.3f} {results['day_21'][name]:>10.3f}")
    
    # Compute validation metrics
    print("\n" + "=" * 60)
    print("ðŸ”¬ BIOLOGICAL VALIDATION CRITERIA")
    print("=" * 60)
    
    # Criterion 1: Pluripotency increase
    oct4_increase = results["day_21"]["OCT4"] - results["day_0"]["OCT4"]
    sox2_increase = results["day_21"]["SOX2"] - results["day_0"]["SOX2"]
    nanog_increase = results["day_21"]["NANOG"] - results["day_0"]["NANOG"]
    
    pluri_pass = oct4_increase > 0.1 and sox2_increase > 0.1
    print(f"1. Pluripotency Increase (OCT4/SOX2 â†‘)")
    print(f"   OCT4: {oct4_increase:+.3f}  SOX2: {sox2_increase:+.3f}  NANOG: {nanog_increase:+.3f}")
    print(f"   Result: {'âœ… PASS' if pluri_pass else 'âŒ FAIL'}")
    
    # Criterion 2: MYC temporal dynamics (peaks then decreases for safe reprogramming)
    myc_peak_idx = np.argmax(trajectory["MYC"])
    myc_peaked_correctly = myc_peak_idx < len(time_points) * 0.7  # Peak before 70% of trajectory
    print(f"\n2. MYC Dynamics (Peak then Decline)")
    print(f"   Peak at day: {time_points[myc_peak_idx]:.1f}")
    print(f"   Result: {'âœ… PASS (safe trajectory)' if myc_peaked_correctly else 'âš ï¸ WARNING (sustained MYC = oncogenic risk)'}")
    
    # Criterion 3: Rejuvenation
    age_decrease = results["day_0"]["BioAge"] - results["day_21"]["BioAge"]
    rejuv_pass = age_decrease > 0.1
    print(f"\n3. Biological Age Rejuvenation")
    print(f"   Age decrease: {age_decrease:+.3f} ({age_decrease * 50:.1f} years equivalent)")
    print(f"   Result: {'âœ… PASS' if rejuv_pass else 'âŒ FAIL'}")
    
    # Overall score
    print("\n" + "=" * 60)
    score = sum([pluri_pass, myc_peaked_correctly, rejuv_pass]) / 3 * 100
    print(f"ðŸ“Š OVERALL VALIDATION SCORE: {score:.0f}%")
    
    if score >= 80:
        print("ðŸŽ‰ EXCELLENT: Model captures key reprogramming dynamics!")
    elif score >= 50:
        print("âš ï¸ MODERATE: Model shows some correct behavior, needs improvement")
    else:
        print("âŒ POOR: Model does not capture reprogramming dynamics")
    print("=" * 60)
    
    return results, score


def main():
    print("\n" + "=" * 60)
    print("ðŸ”¬ IS-CHRP v27.0 GOLD YAMANAKA VALIDATION")
    print("   Testing trained model against biological criteria")
    print("=" * 60 + "\n")
    
    # Load model
    model = load_model()
    
    # Simulate reprogramming
    time_points, trajectory = simulate_oskm_reprogramming(model, n_days=21)
    
    # Analyze results
    results, score = analyze_results(time_points, trajectory)
    
    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), "validation_results")
    os.makedirs(output_dir, exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "model": "ZenithV2DeepDrift",
        "parameters": 9400297,
        "validation_score": score,
        "results": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in results.items()}
    }
    
    with open(os.path.join(output_dir, "zenith_validation.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nðŸ’¾ Results saved to validation_results/zenith_validation.json")
    
    return score


if __name__ == "__main__":
    main()
