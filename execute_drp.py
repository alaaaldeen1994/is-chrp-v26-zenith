
import requests
import numpy as np
import time
import json
import os

# Configuration for Nilus Lab Zenith v27.0 GOLD
BASE_URL = "http://127.0.0.1:9999"
SIM_STEP_ENDPOINT = f"{BASE_URL}/simulate_step"
N_CELLS = 10 

def initialize_population():
    """Initializes Somatic (Slate Gray) population with BioAge 0.80"""
    print("Initializing Baseline: 10 Somatic Cells (Age 0.80)...")
    genes = np.zeros((N_CELLS, 1000), dtype=float)
    genes[:, 40:50] = 0.4 
    genes[:, 90:100] = 0.5 
    
    proteins = genes.copy()
    chromatin = np.zeros((N_CELLS, 1000), dtype=float) + 0.1 
    ages = [0.80] * N_CELLS
    burdens = [0.0] * N_CELLS
    positions = np.random.rand(N_CELLS, 2).flatten().tolist()
    contexts = np.zeros((N_CELLS, 1000), dtype=float).flatten().tolist()
    
    return {
        "genes": genes.flatten().tolist(),
        "proteins": proteins.flatten().tolist(),
        "chromatin": chromatin.flatten().tolist(),
        "ages": ages,
        "burdens": burdens,
        "positions": positions,
        "contexts": contexts,
        "potency": 1.0,
        "vector": None
    }

def execute_drp():
    """MISSION: Decaying Resonance Protocol (DRP) Execution"""
    print("\n--- [MISSION START]: DECAYING RESONANCE PROTOCOL ---")
    
    state = initialize_population()
    
    stages = [
        (4, 10, 14), 
        (4, 8, 16), 
        (4, 6, 18)  
    ]
    
    total_cycle = 1
    
    for cycles, on_h, off_h in stages:
        for _ in range(cycles):
            # Pulse ON
            state["vector"] = "OSKM"
            state["potency"] = 1.0
            for step in range(on_h * 10):
                state = trigger_simulation_step(state)
            
            # Pulse OFF
            state["vector"] = None
            state["potency"] = 0.0
            for step in range(off_h * 10):
                state = trigger_simulation_step(state)
                
            avg_age = sum(state.get("ages", [0])) / N_CELLS
            avg_oct4 = sum(state.get("genes", [0])[0::1000]) / N_CELLS
            print(f"[CYC {total_cycle:02d}] Age: {avg_age:.6f} | OCT4: {avg_oct4:.4f}", flush=True)
            total_cycle += 1
            
    # MISSION AUDIT
    final_age = sum(state["ages"]) / N_CELLS
    final_burden = max(state["burdens"])
    oct4_final = sum(state["genes"][0::1000]) / N_CELLS
    
    print("\n--- [AUDIT REPORT]: PROTOCOL VALIDATION ---")
    print(f"1. Biological Age Reset: {0.80} -> {final_age:.4f}")
    print(f"2. Mutational Burden: {final_burden:.6f}")
    print(f"3. Pluripotency (OCT4): {oct4_final:.4f}")
    
    with open("drp_validation_audit.json", "w") as f:
        json.dump(state, f)
    print("--- [MISSION COMPLETE]: Audit file drp_validation_audit.json saved ---")

def trigger_simulation_step(prev_state):
    try:
        payload = {
            "genes": prev_state["genes"],
            "proteins": prev_state["proteins"],
            "chromatin": prev_state["chromatin"],
            "ages": prev_state["ages"],
            "contexts": prev_state["contexts"],
            "positions": prev_state["positions"],
            "burdens": prev_state["burdens"],
            "vector": prev_state.get("vector"),
            "potency": prev_state.get("potency", 1.0)
        }
        
        response = requests.post(SIM_STEP_ENDPOINT, json=payload, timeout=5)
        if response.status_code == 200:
            res = response.json()
            # Bridge result back to state
            return {
                "genes": res["genes"],
                "proteins": res["proteins"],
                "chromatin": res["chromatin"],
                "ages": res["ages"],
                "burdens": res["burdens"],
                "positions": prev_state["positions"],
                "contexts": prev_state["contexts"],
                "vector": prev_state["vector"],
                "potency": prev_state["potency"]
            }
        else:
            return prev_state
    except Exception:
        return prev_state

if __name__ == "__main__":
    execute_drp()
