import os

def update_manual_with_case_study():
    path = 'how_it_works.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update Discovery Section
    old_discovery = 'Your research intent is processed by our **Zenith-GPT Hybrid Engine**. We translate complex biological goals \n                    (e.g., *"Rejuvenate aged myocardium"*) into high-dimensional vector coordinates within the **scVI latent manifold**.'
    new_discovery = 'Your research intent (e.g., *"Reverse age of HMVECs by 10 years, restore eNOS, suppress SASP, no c-MYC"*) is processed by the **Zenith-GPT Hybrid Engine**. We translate this specific clinical goal into high-dimensional vector coordinates within the **scVI latent manifold**.'
    
    # 2. Update Discovery Details
    old_disc_details = """                    <div class="border-l-2 border-blue-500/30 pl-4 py-2">
                        <span class="text-white">SEMANTIC MAPPING</span><br>GPT-4o converts intent to gene weights.
                    </div>
                    <div class="border-l-2 border-teal-500/30 pl-4 py-2">
                        <span class="text-white">REGULATORY AUDIT</span><br>Verified against 1000+ canonical markers.
                    </div>"""
    
    new_disc_details = """                    <div class="border-l-2 border-blue-500/30 pl-4 py-2">
                        <span class="text-white">HMVEC TARGETING</span><br>Specific targeting of cardiac microvascular niches.
                    </div>
                    <div class="border-l-2 border-teal-500/30 pl-4 py-2">
                        <span class="text-white">ONCOGENIC FILTER</span><br>Strict exclusion of c-MYC and mitogens for ESI 98%.
                    </div>"""

    # 3. Update Latent Arithmetic (The 10-year delta)
    old_latent = 'We compute the **Differential Trajectory** between your current genomic state and the optimized target state.'
    new_latent = 'We compute the **Differential Trajectory** required to reverse the biological age of HMVECs by exactly 10.0 years while restoring eNOS (NOS3) enzymatic activity.'
    
    # 4. Update AF3 section
    old_af3 = 'Predicted factors are validated via **AlphaFold 3 Multimer Analysis**. We generate physical manifests for protein-DNA docking.'
    new_af3 = 'The discovered CRCs (Core Regulatory Complexes) are validated via **AlphaFold 3**. We ensure the non-oncogenic factors exhibit stable docking at the eNOS promoter without mitogenic interference.'
    
    # 5. Update Trials Section
    old_trials = 'Protocols are tested on **1,000+ Digital Twins** using the **Neural SDE Engine**. This simulates the stochasticity of \n                    real human biology before a single drop of reagent is touched.'
    new_trials = 'The HMVEC rejuvenation protocol is tested on **1,000+ Digital Twins**. The **Neural SDE Engine** simulates the suppression of SASP-mediated inflammatory drift across the coronary microvascular niche.'

    # Perform replacements
    content = content.replace(old_discovery, new_discovery)
    content = content.replace(old_disc_details, new_disc_details)
    content = content.replace(old_latent, new_latent)
    content = content.replace(old_af3, new_af3)
    content = content.replace(old_trials, new_trials)
    
    # Update ESI Metrics
    content = content.replace('p-Value Confidence', 'Epigenetic Stability (ESI)')
    content = content.replace('0.0001', '98%')
    
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("Updated How Zenith Works manual with HMVEC Rejuvenation Case Study.")

if __name__ == "__main__":
    update_manual_with_case_study()
