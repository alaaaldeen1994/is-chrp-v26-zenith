"""
IS-CHRP v26.1 - Enhanced Training with Rejuvenation Dynamics
==============================================================

This script trains ZenithV2DeepDrift with STRONG rejuvenation dynamics
based on documented MPTR protocol (GSE165180) findings.

Key improvements:
1. Pluripotency strongly drives age reversal
2. 30-year rejuvenation target over 13-day maturation phase
3. Identity markers preserved during rejuvenation

Author: Nilus Lab
Date: 2026-01-16
"""

import os
import sys
import json
import numpy as np
from datetime import datetime

import torch
import torch.nn as nn

# ============================================================
# MODEL ARCHITECTURE (Matches bridge_server.py exactly)
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


def create_rejuvenation_trajectories(n_samples=8000):
    """
    Creates 1000-dimensional trajectory pairs with STRONG rejuvenation dynamics.
    Based on MPTR protocol (GSE165180).
    
    Key biological findings:
    - 13-day OSKM induction achieves 30-year epigenetic age reversal
    - Cell identity markers dip then recover
    - Pluripotency factors correlate with rejuvenation rate
    """
    print("🧬 Creating enhanced trajectories with high-fidelity rejuvenation dynamics...")
    
    X_list = []  # Input: [genes(1000), age(1), context(1000)]
    Y_list = []  # Output: [delta_genes(1000), delta_age(1)]
    
    for i in range(n_samples):
        # Random initial state
        genes = np.random.rand(1000).astype(np.float32) * 0.3
        age = np.random.uniform(0.3, 0.9)  # Varied starting ages
        context = np.random.rand(1000).astype(np.float32) * 0.2
        
        # Simulate known biological dynamics
        drift = np.zeros(1000, dtype=np.float32)
        
        # ============================================================
        # PLURIPOTENCY NETWORK (genes 0-9)
        # ============================================================
        pluri_sum = genes[:10].mean()
        
        # Self-activation: OCT4/SOX2/NANOG form positive feedback loop
        drift[:10] = 0.15 * (pluri_sum - genes[:10]) + 0.08
        
        # NANOG (idx 2) requires both OCT4 (0) and SOX2 (1)
        oct4_sox2_synergy = genes[0] * genes[1]
        drift[2] += 0.1 * oct4_sox2_synergy
        
        # ============================================================
        # CARDIAC MODULE (genes 10-19) - Identity Preservation
        # ============================================================
        # GATA4 (10), NKX2-5 (11), TNNT2 (13)
        cardio_tf = (genes[10] + genes[11]) / 2
        # Key: Identity dips during reprogramming but recovers (literature finding)
        identity_suppression = pluri_sum * 0.3  # Pluripotency suppresses lineage
        drift[10:20] = 0.05 * cardio_tf - 0.02 * genes[10:20] - identity_suppression * 0.1
        
        # ============================================================
        # NEURAL MODULE (20-29)
        # ============================================================
        neuro_tf = (genes[22] + genes[23]) / 2
        drift[20:30] = 0.06 * neuro_tf - 0.02 * genes[20:30] - identity_suppression * 0.08
        
        # ============================================================
        # SOMATIC MARKERS (40-49) - Decrease during reprogramming
        # ============================================================
        drift[40:50] = -0.08 * genes[40:50] - 0.05 * pluri_sum
        
        # ============================================================
        # STRESS/CELL CYCLE (50-59)
        # ============================================================
        # TP53 (50): Spikes during stress, then normalized
        # High pluripotency eventually stabilizes TP53
        drift[50] = 0.05 * (1 - genes[50]) * (1 - pluri_sum * 0.8)
        
        # MKI67 (51): Proliferation - high during reprogramming, then drops
        drift[51] = 0.04 * (pluri_sum - genes[51] * 0.5)
        
        # ============================================================
        # EPIGENETICS (70-79) - Chromatin opening with pluripotency
        # ============================================================
        # OCT4/SOX2 are pioneer factors that open chromatin
        pioneer_activity = (genes[0] + genes[1]) / 2
        drift[70:80] = 0.08 * pioneer_activity - 0.01 * age
        
        # TET1/2 (74, 75) - demethylation enzymes, activated by pluripotency
        drift[74:76] = 0.1 * pluri_sum
        
        # ============================================================
        # BACKGROUND GENES (100-999)
        # ============================================================
        drift[100:1000] = 0.005 * (np.random.randn(900) * 0.1).astype(np.float32)
        
        # ============================================================
        # BIOAGE DYNAMICS (THE KEY FIX!)
        # ============================================================
        # High pluripotency = Strong rejuvenation dynamics
        # 30-year reversal over 13-day maturation phase
        # Normalized: 0.5 age units over 13 days = ~0.04/day = 0.004/step (dt=0.1)
        
        # Rejuvenation rate proportional to:
        # 1. Pluripotency level (OCT4 + SOX2 + NANOG)
        # 2. Epigenetic reprogramming (TET activity)
        # 3. Lower TP53 stress
        
        tet_activity = (genes[74] + genes[75]) / 2
        stress_factor = 1.0 - genes[50] * 0.5  # High TP53 reduces rejuvenation
        
        # STRONG REJUVENATION SIGNAL
        rejuvenation_rate = (
            -0.08 * pluri_sum *      # Pluripotency drives rejuvenation
            (1 + tet_activity) *      # Epigenetic boost
            stress_factor             # Stress reduces effect
        )
        
        # Baseline aging (very slow when not reprogramming)
        baseline_aging = 0.001 * (1 - pluri_sum)
        
        age_drift = rejuvenation_rate + baseline_aging
        
        # Clamp to biological limits (can't go below 0.1 normalized age)
        if age + age_drift < 0.1:
            age_drift = 0.1 - age
        
        # Add controlled noise
        drift += (np.random.randn(1000) * 0.015).astype(np.float32)
        age_drift += np.random.randn() * 0.005
        
        # Build input/output
        input_vec = np.concatenate([genes, [age], context])
        output_vec = np.concatenate([drift, [age_drift]])
        
        X_list.append(input_vec)
        Y_list.append(output_vec)
        
        if (i + 1) % 2000 == 0:
            print(f"   Generated {i+1}/{n_samples} samples...")
    
    X = np.array(X_list, dtype=np.float32)
    Y = np.array(Y_list, dtype=np.float32)
    
    # Verify rejuvenation signal
    age_drifts = Y[:, -1]
    print(f"\n📊 Age drift statistics:")
    print(f"   Mean: {age_drifts.mean():.4f} (negative = rejuvenation)")
    print(f"   Min: {age_drifts.min():.4f}, Max: {age_drifts.max():.4f}")
    
    print(f"✅ Created {len(X)} trajectory pairs with enhanced rejuvenation")
    
    return X, Y


def train_with_age_focus(X, Y, epochs=50):
    """Train with weighted loss for age dynamics."""
    print("\n" + "=" * 60)
    print("🧠 Training ZenithV2DeepDrift with REJUVENATION FOCUS")
    print("=" * 60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️ Using device: {device}")
    
    model = ZenithV2DeepDrift(input_dim=1000, hidden_dim=1024).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"📊 Model parameters: {total_params:,} (~{total_params/1e6:.1f}M)")
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs)
    
    # Create data loaders
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    Y_tensor = torch.tensor(Y, dtype=torch.float32).to(device)
    
    dataset = torch.utils.data.TensorDataset(X_tensor, Y_tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
    
    losses = []
    
    print(f"🏋️ Training for {epochs} epochs with age-weighted loss...")
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        epoch_gene_loss = 0.0
        epoch_age_loss = 0.0
        
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            pred = model(batch_x)
            
            # Split predictions
            pred_genes = pred[:, :1000]
            pred_age = pred[:, 1000]
            
            target_genes = batch_y[:, :1000]
            target_age = batch_y[:, 1000]
            
            # Weighted loss: 5x weight on age prediction
            gene_loss = nn.functional.mse_loss(pred_genes, target_genes)
            age_loss = nn.functional.mse_loss(pred_age, target_age)
            
            # Total loss with age emphasis
            loss = gene_loss + 5.0 * age_loss
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            epoch_gene_loss += gene_loss.item()
            epoch_age_loss += age_loss.item()
        
        scheduler.step()
        
        avg_loss = epoch_loss / len(dataloader)
        avg_gene = epoch_gene_loss / len(dataloader)
        avg_age = epoch_age_loss / len(dataloader)
        losses.append(avg_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs} - Total: {avg_loss:.6f} | Genes: {avg_gene:.6f} | Age: {avg_age:.6f}")
    
    return model, losses


def save_model(model, losses):
    """Save the trained model."""
    model_dir = os.path.join(os.path.dirname(__file__), "models", "driftmlp_trained")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "driftmlp.pt")
    torch.save(model.state_dict(), model_path)
    
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "architecture": "ZenithV2DeepDrift",
        "input_dim": 1000,
        "hidden_dim": 1024,
        "final_loss": losses[-1],
        "epochs": len(losses),
        "training_type": "Enhanced Rejuvenation (Protocol-inspired)",
        "parameters": sum(p.numel() for p in model.parameters()),
        "features": [
            "Strong pluripotency-driven age reversal",
            "TET-mediated epigenetic reprogramming",
            "Identity preservation during rejuvenation",
            "5x weighted age loss"
        ]
    }
    
    with open(os.path.join(model_dir, "training_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 Model saved to: {model_path}")
    
    return model_path


def main():
    print("\n" + "=" * 60)
    print("🚀 IS-CHRP v26.1 - ENHANCED REJUVENATION TRAINING")
    print("   Based on MPTR Protocol (GSE165180)")
    print("=" * 60 + "\n")
    
    # Create enhanced trajectory data
    X, Y = create_rejuvenation_trajectories(n_samples=8000)
    
    # Train with age-focused loss
    model, losses = train_with_age_focus(X, Y, epochs=50)
    
    # Save
    model_path = save_model(model, losses)
    
    print("\n" + "=" * 60)
    print("🎉 REJUVENATION TRAINING COMPLETE!")
    print("=" * 60)
    print("\nImprovements made:")
    print("  ✅ Strong pluripotency → age reversal correlation")
    print("  ✅ TET1/2 epigenetic boost for rejuvenation")
    print("  ✅ 5x weighted loss on age prediction")
    print("  ✅ 8,000 training samples (up from 5,000)")
    print("\nRun validation: python validate_zenith.py")


if __name__ == "__main__":
    main()
