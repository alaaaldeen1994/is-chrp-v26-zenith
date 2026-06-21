import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bridge_server import app

client = TestClient(app)

def test_endpoints():
    print("Testing GraphRAG query endpoint...")
    response = client.post("/api/v1/clinical/graphrag/query", json={
        "query": "Show me MEF2C and GATA4 interactions with MYC",
        "top_k_subgraphs": 5,
        "confidence_threshold": 0.75
    })
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200

    print("\nTesting Perturbation prediction endpoint...")
    response = client.post("/api/v1/clinical/predict/perturbation", json={
        "baseline_cell_type": "fibroblast",
        "perturbation_factors": {
            "GATA4": 1.2,
            "MEF2C": 0.8,
            "TBX5": 1.0,
            "NKX2-5": 0.5,
            "MYC": 0.0
        }
    })
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200

    print("\nTesting LNP optimization endpoint...")
    response = client.post("/api/v1/clinical/delivery/lnp-optimize", json={
        "molar_ratios": {
            "ionizable": 50.0,
            "cholesterol": 38.5,
            "helper": 10.0,
            "peg": 1.5
        },
        "np_ratio": 6.0
    })
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200

    print("\nTesting Pipeline telemetry endpoint...")
    response = client.post("/api/v1/clinical/pipeline/telemetry", json={
        "metrics_json": '{"total_reads": 1000000, "mapped_reads": 850000, "mitochondrial_reads": 50000, "cell_count": 5000}'
    })
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200

    print("\nTesting Automation protocol endpoint...")
    response = client.post("/api/v1/clinical/automation/generate", json={
        "source_well": "A1",
        "cocktail": {
            "GATA4": 1.0,
            "MEF2C": 1.5
        }
    })
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200

    print("\nAll integration tests passed successfully!")

if __name__ == "__main__":
    test_endpoints()
