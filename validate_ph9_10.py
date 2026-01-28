import requests
import numpy as np
import time

ENDPOINT = "http://127.0.0.1:9999"

def test_multi_omics_sync():
    print("Testing Multi-Omics Sync...")
    # Create 10 dummy cells
    n = 10
    payload = {
        "genes": [0.5] * (n * 16),
        "proteins": [0.5] * (n * 16),
        "chromatin": [1.0] * (n * 16),
        "ages": [0.5] * n,
        "contexts": [0.5] * (n * 16),
        "vector": "OSKM"
    }
    
    try:
        r = requests.post(f"{ENDPOINT}/simulate_step", json=payload)
        r.raise_for_status()
        data = r.json()
        
        # Verify response structure
        assert "genes" in data
        assert "proteins" in data
        assert "chromatin" in data
        assert len(data["genes"]) == n * 16
        print("SUCCESS: Multi-Omics Sync Successful")
        
        # Verify Protein Lag (Proteins should not equal Genes in one jump if lag is working)
        # Note: In bridge_server, translation_rate = 0.15
        p0 = data["proteins"][0]
        g0 = data["genes"][0]
        print(f"DEBUG: Gene[0]={g0:.4f}, Protein[0]={p0:.4f}")
        if abs(p0 - g0) > 0.001:
            print("SUCCESS: Protein Lag Detected (Inertia Working)")
        else:
            print("WARNING: Protein Lag Minimal or Absent")

    except Exception as e:
        print(f"ERROR: Multi-Omics Test Failed: {e}")

def test_systems_biology_signaling():
    print("\nTesting Systems Biology (Cardio -> Neuro Signaling)...")
    # 2 cells: Cell 0 is Cardio, Cell 1 is Neuro
    # Cardio marker: TNNT2 (index 5)
    # Neuro marker: NEUROD2 (index 9), CHRNA1 (index 11)
    
    n = 2
    genes = [0.0] * (n * 16)
    proteins = [0.0] * (n * 16)
    chromatin = [1.0] * (n * 16)
    
    # Cell 0: Cardio
    proteins[5] = 0.9 
    genes[5] = 0.9
    
    # Cell 1: Neuro
    proteins[16 + 9] = 0.9 # High NeuroD2
    genes[16 + 9] = 0.9
    chrna1_start = proteins[16 + 11] # CHRNA1
    
    payload = {
        "genes": genes,
        "proteins": proteins,
        "chromatin": chromatin,
        "ages": [0.5] * n,
        "contexts": [0.0] * (n * 16),
        "vector": None
    }
    
    try:
        r = requests.post(f"{ENDPOINT}/simulate_step", json=payload)
        r.raise_for_status()
        data = r.json()
        
        chrna1_end = data["proteins"][16 + 11]
        print(f"DEBUG: CHRNA1 Before: {chrna1_start:.4f}, After: {chrna1_end:.4f}")
        
        if chrna1_end > chrna1_start:
            print("SUCCESS: Systems Signaling Detected (Cardio -> Neuro Flux Active)")
        else:
            print("WARNING: Systems Signaling Absent or Below Threshold")
            
    except Exception as e:
        print(f"ERROR: Systems Biology Test Failed: {e}")

if __name__ == "__main__":
    # Ensure bridge_server is running!
    # Note: If it's the old version, it will return 422 Unprocessable Entity
    test_multi_omics_sync()
    test_systems_biology_signaling()
