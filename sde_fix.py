import os

def apply_sde_logic():
    path = 'bridge_server.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old_logic = """        with torch.no_grad():
            for step in range(5):
                # Apply Stochastic Drift (Simulating Neural SDE)
                drift_noise = torch.randn(N, 1000) * 0.02
                
                # Active Arm: Perturbation + Drift
                active_drift = (perturbation.expand(N, -1) * 0.15) + drift_noise
                active_cohort = torch.clamp(active_cohort + active_drift, 0, 1)
                
                # Placebo Arm: Only Drift (Degradation)
                placebo_drift = (torch.randn(N, 1000) * 0.01) + drift_noise
                placebo_cohort = torch.clamp(placebo_cohort + placebo_drift, 0, 1)"""
                
    new_logic = """        with torch.no_grad():
            dt = 0.2  # Time step
            for step in range(5):
                # NEURAL SDE FORM: dx = f(x,t)dt + g(x,t)dW
                # f(x,t) = Deterministic Drift (Perturbation Toward Target)
                # g(x,t) = Stochastic Diffusion (Manifold Noise)
                
                # 1. Diffusion Coefficient (Wiener Process)
                dW = torch.randn(N, 1000) * np.sqrt(dt)
                g_active = 0.05  # Diffusion scaling for Active arm
                g_placebo = 0.08 # Higher diffusion (instability) for Placebo
                
                # 2. Active Arm Update
                f_active = perturbation.expand(N, -1) * 0.5 
                dx_active = (f_active * dt) + (g_active * dW)
                active_cohort = torch.clamp(active_cohort + dx_active, 0, 1)
                
                # 3. Placebo Arm Update (Drift is 0 or degradation-focused)
                f_placebo = torch.randn(N, 1000) * -0.01 # Slight degradation drift
                dx_placebo = (f_placebo * dt) + (g_placebo * dW)
                placebo_cohort = torch.clamp(placebo_cohort + dx_placebo, 0, 1)"""
                
    if old_logic in content:
        new_content = content.replace(old_logic, new_logic)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print("Successfully implemented Neural SDE logic.")
    else:
        # Fuzzy match (handle indentation/newlines)
        print("Exact match failed. Attempting fuzzy match...")
        import re
        pattern = r"with torch\.no_grad\(\):\s+for step in range\(5\):.*?placebo_cohort = torch\.clamp\(placebo_cohort \+ placebo_drift, 0, 1\)"
        new_content = re.sub(pattern, new_logic, content, flags=re.DOTALL)
        if new_content != content:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
            print("Successfully implemented Neural SDE logic (Fuzzy Match).")
        else:
            print("Fuzzy match failed.")

if __name__ == "__main__":
    apply_sde_logic()
