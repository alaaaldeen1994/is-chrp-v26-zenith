import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path so we can import bridge_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge_server import app

def test_integration_endpoints():
    print("=== RUNNING FASTAPI ENDPOINT INTEGRATION TESTS ===")
    
    client = TestClient(app)
    
    # Test the AF3 Manifest generation endpoint with KLF4 and SIRT1
    print("\nCalling /api/v1/clinical/af3-manifest for KLF4 and SIRT1...")
    response = client.post("/api/v1/clinical/af3-manifest", json={
        "factors": ["KLF4", "SIRT1"],
        "dna_motif": "CCTGTGACTGTGGGGTTCACGCTCCCGGGTG"
    })
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    
    # Assert manifest structure
    assert "name" in data, "Manifest name missing"
    assert "sequences" in data, "Manifest sequences missing"
    
    sequences = data["sequences"]
    print(f"Manifest Name: {data['name']}")
    print(f"Number of chains: {len(sequences)}")
    assert len(sequences) == 3, f"Expected 3 chains (1 protein, 2 DNA), got {len(sequences)}"
    
    # Validate protein sequence
    protein_chain = sequences[0]
    assert "protein" in protein_chain, "First chain is not a protein chain"
    fused_seq = protein_chain["protein"]["sequence"]
    
    # The length of KLF4 domain (128) + Z-linker (15) + SIRT1 domain (270) should be exactly 413!
    print(f"Generated Protein Sequence Length: {len(fused_seq)} (Expected: 413)")
    assert len(fused_seq) == 413, f"Expected fused sequence length of 413, got {len(fused_seq)}"
    
    # Confirm it starts with KLF4-like sequence and ends with SIRT1-like sequence
    # and has the linker in the middle
    assert fused_seq[128:143] == "GGGGSGGGGSGGGGS", "Z-linker is not present at the correct position"
    print("Z-linker check: PASS")
    
    # Validate DNA chains
    dna_chain_1 = sequences[1]
    dna_chain_2 = sequences[2]
    assert "dna" in dna_chain_1
    assert "dna" in dna_chain_2
    
    print(f"DNA Chain 1 Sequence: {dna_chain_1['dna']['sequence']}")
    print(f"DNA Chain 2 Sequence: {dna_chain_2['dna']['sequence']}")
    
    print("\nINTEGRATION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_integration_endpoints()
