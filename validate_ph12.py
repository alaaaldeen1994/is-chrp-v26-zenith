import time
import requests
import numpy as np

# Configuration
BRIDGE_URL = "http://127.0.0.1:9999"

def test_malignancy_trigger():
    print("--- Testing Phase 12: Oncogenic Transformation ---")
    
    n_agents = 2000 # Increase population to trigger stochastic events
    # Flattened arrays for BatchCellState
    genes = [0.1] * (16 * n_agents)
    proteins = [0.1] * (16 * n_agents)
    chromatin = [1.0] * (16 * n_agents)
    ages = [0.9] * n_agents # Stressed
    contexts = [0.1] * (16 * n_agents)
    
    # All agents have low TP53
    for i in range(n_agents):
        genes[i*16 + 7] = 0.01 
        proteins[i*16 + 7] = 0.01
    
    payload = {
        "genes": genes,
        "proteins": proteins,
        "chromatin": chromatin,
        "ages": ages,
        "contexts": contexts,
        "vector": "NONE",
        "partial_mode": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BRIDGE_URL}/simulate_step", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Sim step for {n_agents} agents completed in {((end_time - start_time)*1000):.2f}ms (Mode: {data.get('mode')})")
            
            # Check if any agent has MYC (index 3) > 0.4
            new_genes = np.array(data['genes']).reshape(n_agents, 16)
            max_myc = np.max(new_genes[:, 3])
            print(f"Max MYC in population: {max_myc:.4f}")
            
            if max_myc > 0.4:
                print("Observed at least one oncogenic spike in the population.")
            else:
                print("No oncogenic spikes in this frame (Stochastic).")
                
            if 'proteins' in data and 'chromatin' in data:
                print("Multi-Omics state returned successfully.")
        else:
            print(f"FAILED: Server returned {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: Could not connect to bridge server: {e}")

if __name__ == "__main__":
    test_malignancy_trigger()
