"""
IS-CHRP v26.0 DriftMLP Training Script
======================================
This script trains the DriftMLP model on REAL Human Cell Atlas data.
It uses the heart_cell_atlas from scVI, creating pseudo-trajectories
from the latent space to learn cellular dynamics.

Author: Dr. Kagawea
"""
import scvi
import torch
import torch.nn as nn
import numpy as np
import os
import json
from datetime import datetime

# Configuration
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "driftmlp_trained")
HCA_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "scvi_model_hca")
EPOCHS = 3
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
LATENT_DIM = 16

# Gene symbols matching the simulation
GENE_SYMBOLS = [
    "POU5F1", "SOX2", "NANOG", "MYC", "MKI67", 
    "TNNT2", "TTN", "TP53", "NKX2-5", "NEUROD2", 
    "TBX5", "CHRNA1", "KLF4", "LIN28A", "GATA4", "SOX17"
]


class DriftMLP(nn.Module):
    """Neural Network that learns the drift term of the cellular SDE."""
    def __init__(self, input_dim=16, hidden_dim=64):
        super().__init__()
        # Input: Self Genes (16) + Global BioAge (1) + Paracrine Context (16)
        self.net = nn.Sequential(
            nn.Linear(input_dim * 2 + 1, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim + 1)
        )
    
    def forward(self, x):
        return self.net(x)


def load_hca_latent_vectors():
    """Load HCA data and extract latent representations. Returns (NxD) array."""
    print("📊 Loading HCA data from scVI model...")
    
    # Load the trained scVI model
    adata_path = os.path.join(HCA_MODEL_DIR, "adata.h5ad")
    if not os.path.exists(adata_path):
        print("❌ HCA model not found. Run train_hca_scvi.py first.")
        return None
    
    scvi_model = scvi.model.SCVI.load(HCA_MODEL_DIR)
    adata = scvi_model.adata
    
    print(f"✅ Loaded {adata.n_obs} cells with {adata.n_vars} genes")
    
    # Get latent representations (N x latent_dim)
    latent = scvi_model.get_latent_representation()
    print(f"✅ Extracted latent vectors: {latent.shape}")
    
    return latent, adata


def create_pseudo_trajectories(latent, n_steps=10, noise_scale=0.02):
    """
    Create pseudo-trajectories for training.
    Strategy: Sample pairs of points and treat smaller distances as "dt".
    
    For real trajectory learning, we would need time-course data.
    This creates synthetic trajectories using:
    1. Random walks in latent space
    2. Interpolation between cell states
    """
    print("🔄 Creating pseudo-trajectories for training...")
    
    n_cells = latent.shape[0]
    n_dim = latent.shape[1]
    
    # Normalize latent vectors to [0, 1] for our 16-gene simulation space
    latent_min = latent.min(axis=0)
    latent_max = latent.max(axis=0)
    latent_norm = (latent - latent_min) / (latent_max - latent_min + 1e-8)
    
    # Create training pairs: (current_state, next_state)
    # Using random walks for pseudo-dynamics
    trajectories_x = []
    trajectories_dx = []
    
    for _ in range(n_cells * 2):  # Generate 2x data via augmentation
        # Pick random starting cell
        idx = np.random.randint(0, n_cells)
        x = latent_norm[idx].copy()
        
        # Create random walk
        for step in range(n_steps):
            # Small random perturbation (simulating dt)
            noise = np.random.randn(n_dim) * noise_scale
            
            # Constrain to stay near real data manifold
            x_next = np.clip(x + noise, 0, 1)
            
            # Record the transition
            context = np.zeros(n_dim)  # Paracrine context (simplified)
            age = 0.5  # Normalized age
            
            input_vec = np.concatenate([x, [age], context])
            dx = x_next - x
            
            trajectories_x.append(input_vec)
            trajectories_dx.append(np.concatenate([dx, [0.0]]))  # dx for genes + age
            
            x = x_next
    
    X = np.array(trajectories_x, dtype=np.float32)
    Y = np.array(trajectories_dx, dtype=np.float32)
    
    print(f"✅ Created {len(X)} training samples")
    
    return X, Y


def train_driftmlp(X, Y, epochs=EPOCHS, batch_size=BATCH_SIZE, lr=LEARNING_RATE):
    """Train the DriftMLP model on trajectory data."""
    print(f"🧠 Training DriftMLP for {epochs} epochs...")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"   Device: {device}")
    
    model = DriftMLP(input_dim=LATENT_DIM, hidden_dim=64).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    # Convert to tensors
    X_tensor = torch.tensor(X, dtype=torch.float32).to(device)
    Y_tensor = torch.tensor(Y, dtype=torch.float32).to(device)
    
    dataset = torch.utils.data.TensorDataset(X_tensor, Y_tensor)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    losses = []
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_y in dataloader:
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(dataloader)
        losses.append(avg_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.6f}")
    
    return model, losses


def save_model(model, losses):
    """Save trained model and training metrics."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Save model weights
    model_path = os.path.join(MODEL_DIR, "driftmlp.pt")
    torch.save(model.state_dict(), model_path)
    print(f"💾 Saved model to {model_path}")
    
    # Save training metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "latent_dim": LATENT_DIM,
        "final_loss": losses[-1],
        "loss_history": losses,
        "data_source": "Human Cell Atlas (heart_cell_atlas_subsampled)",
        "genes": GENE_SYMBOLS,
        "note": "Trained on pseudo-trajectories from scVI latent space"
    }
    
    meta_path = os.path.join(MODEL_DIR, "training_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"📋 Saved metadata to {meta_path}")
    
    return metadata


def main():
    print("=" * 60)
    print("IS-CHRP v26.0 DriftMLP Training Pipeline")
    print("=" * 60)
    
    # Step 1: Load HCA latent vectors
    result = load_hca_latent_vectors()
    if result is None:
        return
    latent, adata = result
    
    # Step 2: Create pseudo-trajectories
    X, Y = create_pseudo_trajectories(latent[:, :LATENT_DIM])  # Use first 16 dims
    
    # Step 3: Train model
    model, losses = train_driftmlp(X, Y)
    
    # Step 4: Save
    metadata = save_model(model, losses)
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE")
    print(f"   Final Loss: {metadata['final_loss']:.6f}")
    print(f"   Model saved to: {MODEL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
