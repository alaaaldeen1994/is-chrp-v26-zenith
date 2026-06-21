import json
import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add workspace directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from bridge_server import app

def test_reprogramming():
    client = TestClient(app)
    
    # Request payload
    payload = {
        "current_genes": [0.1] * 4908,
        "target_query": "Reprogram mural pericytes into functional capillary endothelial cells to restore blood flow and reduce microvascular leakage.",
        "cell_type": "pericyte",
        "repro_mode": "full",
        "safety_level": "balanced",
        "bio_age": 0.5
    }
    
    print("Sending reprogramming query to /discover_hybrid...")
    response = client.post("/discover_hybrid", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n=== SUCCESS: REPROGRAMMING DISCOVERY RESULTS ===")
        print(f"Recommended Protocol: {data.get('recommended_protocol')}")
        print(f"Confidence Score: {data.get('confidence')}")
        print(f"Oncogenic Risk: {data.get('oncogenic_risk_label')} ({data.get('oncogenic_risk')})")
        print(f"Epigenetic Age Reduction: {data.get('epigenetic_age_reduction')} years")
        
        print("\nRecommended Transcription Factors (Target Profile):")
        profile = data.get("target_profile", {})
        for gene, val in sorted(profile.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {gene}: {val}")
            
        print("\nScientific Rationale:")
        print(data.get("scientific_rationale"))
        
        # Save output for inspection
        output_file = "scratch/pericyte_reprogramming_result.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nFull result saved to {output_file}")
    else:
        print(f"\n=== FAILURE: Status Code {response.status_code} ===")
        print(response.text)

if __name__ == "__main__":
    test_reprogramming()
