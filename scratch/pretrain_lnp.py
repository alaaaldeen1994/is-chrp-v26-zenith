import sys
import os
import torch
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.lnp_optimizer import LNPOptimizerService

def pretrain_and_save():
    print("============================================================")
    print("Pre-training LNP PyTorch Surrogate Model for Production...")
    
    # 1. Instantiate the service, which generates data and trains the model
    service = LNPOptimizerService()
    
    # 2. Extract model and parameters
    model = service.model
    x_mean = service.x_mean
    x_std = service.x_std
    y_mean = service.y_mean
    y_std = service.y_std
    
    # 3. Create a checkpoint dictionary
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'x_mean': torch.tensor(x_mean, dtype=torch.float32),
        'x_std': torch.tensor(x_std, dtype=torch.float32),
        'y_mean': torch.tensor(y_mean, dtype=torch.float32),
        'y_std': torch.tensor(y_std, dtype=torch.float32)
    }
    
    # 4. Save checkpoint to models/ directory
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'lnp_surrogate.weights')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    torch.save(checkpoint, output_path)
    print(f"[SUCCESS] Saved pre-trained weights and scaling parameters to: {output_path}")
    print("============================================================")

if __name__ == "__main__":
    pretrain_and_save()
