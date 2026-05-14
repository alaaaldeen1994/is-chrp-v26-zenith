import os

def final_crash_repair():
    path = 'bridge_server.py'
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Surgical repair of the SDE block indentation (around line 5770)
    # The block should be aligned with the preceding 'elif' blocks.
    # Looking at the code, it seems the 'with torch.no_grad():' was over-indented.
    
    new_lines = []
    for i, line in enumerate(lines):
        # Detect the specific broken block
        if "with torch.no_grad():" in line and "dt = 0.2" in lines[i+1]:
            # Force correct indentation (8 spaces for method body)
            new_lines.append("        with torch.no_grad():\n")
        elif "dt = 0.2  # Time step" in line:
            new_lines.append("            dt = 0.2  # Time step\n")
        elif "for step in range(5):" in line and "NEURAL SDE" in lines[i+1]:
            new_lines.append("            for step in range(5):\n")
        elif "# NEURAL SDE FORM" in line:
            new_lines.append("                # NEURAL SDE FORM: dx = f(x,t)dt + g(x,t)dW\n")
        elif "# f(x,t) =" in line:
            new_lines.append("                # f(x,t) = Deterministic Drift (Perturbation Toward Target)\n")
        elif "# g(x,t) =" in line:
            new_lines.append("                # g(x,t) = Stochastic Diffusion (Manifold Noise)\n")
        elif "# 1. Diffusion Coefficient" in line:
            new_lines.append("                # 1. Diffusion Coefficient (Wiener Process)\n")
        elif "dW = torch.randn" in line and "sqrt(dt)" in line:
            new_lines.append("                dW = torch.randn(N, 1000) * np.sqrt(dt)\n")
        elif "g_active = 0.05" in line:
            new_lines.append("                g_active = 0.05  # Diffusion scaling for Active arm\n")
        elif "g_placebo = 0.08" in line:
            new_lines.append("                g_placebo = 0.08 # Higher diffusion (instability) for Placebo\n")
        elif "# 2. Active Arm Update" in line:
            new_lines.append("                # 2. Active Arm Update\n")
        elif "f_active = perturbation" in line:
            new_lines.append("                f_active = perturbation.expand(N, -1) * 0.5 \n")
        elif "dx_active = (f_active * dt)" in line:
            new_lines.append("                dx_active = (f_active * dt) + (g_active * dW)\n")
        elif "active_cohort = torch.clamp(active_cohort + dx_active" in line:
            new_lines.append("                active_cohort = torch.clamp(active_cohort + dx_active, 0, 1)\n")
        elif "# 3. Placebo Arm Update" in line:
            new_lines.append("                # 3. Placebo Arm Update (Drift is 0 or degradation-focused)\n")
        elif "f_placebo = torch.randn" in line:
            new_lines.append("                f_placebo = torch.randn(N, 1000) * -0.01 # Slight degradation drift\n")
        elif "dx_placebo = (f_placebo * dt)" in line:
            new_lines.append("                dx_placebo = (f_placebo * dt) + (g_placebo * dW)\n")
        elif "placebo_cohort = torch.clamp(placebo_cohort + dx_placebo" in line:
            new_lines.append("                placebo_cohort = torch.clamp(placebo_cohort + dx_placebo, 0, 1)\n")
        else:
            new_lines.append(line)
            
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(new_lines)
    print("Surgically repaired indentation in bridge_server.py")

if __name__ == "__main__":
    final_crash_repair()
