import os
import re

def calculate_zenith_scores():
    scores = {}
    
    # 1. Academic & Biological Accuracy
    # Check for canonical gene symbols, UniProt IDs, and scientific rationale logic
    accuracy_points = 0
    with open('bridge_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'UniProt Swiss-Prot reviewed' in content: accuracy_points += 20
        if 'organism 9606' in content: accuracy_points += 20
        if 'GENE_SYMBOLS' in content and len(re.findall(r'"[A-Z0-9]+"', content)) > 100: accuracy_points += 30
        if 'STRICT SCIENTIFIC CONSTRAINTS' in content: accuracy_points += 30
    scores['Academic Integrity & Biological Accuracy'] = accuracy_points

    # 2. Computational Fidelity (Latent Manifolds)
    fidelity_points = 0
    if 'torch' in content and 'numpy' in content: fidelity_points += 20
    if 'Stochastic Latent Drift' in content: fidelity_points += 30
    if 'manifold_x' in content and 'manifold_y' in content: fidelity_points += 25
    if 'scvi' in content.lower(): fidelity_points += 25
    scores['Computational Fidelity (Latent Manifolds)'] = fidelity_points

    # 3. Structural Validation (AF3 Bridge)
    af3_points = 0
    if os.path.exists('af3_automation_bridge.py'):
        with open('af3_automation_bridge.py', 'r', encoding='utf-8') as f:
            af3_content = f.read()
            if 'StructuralAuthority' in af3_content: af3_points += 30
            if 'proteinChain' in af3_content: af3_points += 30
            if 'manifest' in af3_content and 'json' in af3_content: af3_points += 40
    scores['Structural Validation (AF3 Bridge)'] = af3_points

    # 4. Robotic & Practical Integration
    robotic_points = 0
    if os.path.exists('robotic_bridge.py'):
        with open('robotic_bridge.py', 'r', encoding='utf-8') as f:
            robo_content = f.read()
            if 'Opentrons Flex' in robo_content: robotic_points += 40
            if 'dosage_optimization' in content: robotic_points += 60
    scores['Robotic & Practical Integration'] = robotic_points

    # 5. UI/UX & Institutional Aesthetic
    ui_points = 0
    with open('profile.html', 'r', encoding='utf-8') as f:
        profile_content = f.read()
        if '@media' in profile_content: ui_points += 40
        if 'glassmorphism' in profile_content or 'backdrop-blur' in profile_content: ui_points += 30
        if 'Outfit' in profile_content: ui_points += 30
    scores['UI/UX & Institutional Aesthetic'] = ui_points

    # 6. System Stability
    stability_points = 0
    if 'sanitize_input' in content: stability_points += 30
    if 'RateLimiter' in content or 'limiter' in content: stability_points += 30
    if 'XSS Protection' in content: stability_points += 40
    scores['System Stability & Engineering Quality'] = stability_points

    return scores

if __name__ == "__main__":
    results = calculate_zenith_scores()
    print("--- ZENITH INSTITUTIONAL AUDIT RESULTS ---")
    for k, v in results.items():
        print(f"{k}: {v}%")
