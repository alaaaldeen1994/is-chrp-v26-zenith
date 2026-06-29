import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bridge_server import app

client = TestClient(app)

# Use the test key generated during setup
TEST_API_KEY = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"

def test_api_v1():
    print("="*60)
    print("RUNNING API V1 SYSTEM INTEGRATION TESTS")
    print("="*60)

    # 1. Test Health endpoint (unauthenticated)
    print("\n[TEST] GET /api/v1/health (should be public)...")
    response = client.get("/api/v1/health")
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "online"

    # 2. Test LNP Optimize endpoint (should reject with 401 if unauthenticated)
    print("\n[TEST] POST /api/v1/lnp/optimize (without key)...")
    response = client.post("/api/v1/lnp/optimize", json={
        "molar_ratios": {"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
        "np_ratio": 6.0
    })
    print("Status:", response.status_code)
    assert response.status_code == 401
    print("[PASS] Successfully rejected unauthenticated request.")

    # 3. Test LNP Optimize endpoint (authenticated)
    print("\n[TEST] POST /api/v1/lnp/optimize (with valid key)...")
    response = client.post(
        "/api/v1/lnp/optimize", 
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "molar_ratios": {"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
            "np_ratio": 6.0,
            "active_ligand_conjugation": False,
            "ligand_density": 0.0,
            "peg_mw": 2000.0
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    assert "circulation_half_life_hours" in response.json()["data"]
    print("[PASS] Successfully predicted LNP parameters.")

    # 4. Test Safety Audit endpoint (authenticated)
    print("\n[TEST] POST /api/v1/safety/audit (with valid key)...")
    response = client.post(
        "/api/v1/safety/audit",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "factors": ["GATA4", "OCT4", "MYC"]
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    assert "sirtuin_engagement" in response.json()["data"]
    assert "horvath_clock_impact" in response.json()["data"]
    print("[PASS] Successfully evaluated safety profile.")

    # 5. Test Async Discovery job
    print("\n[TEST] POST /api/v1/discover/run (async job)...")
    response = client.post(
        "/api/v1/discover/run",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "target_query": "cardiac rejuvenation",
            "cell_type": "ventricular_myocyte"
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    status_url = response.json()["status_url"]
    assert job_id is not None
    print(f"[PASS] Successfully queued discovery job: {job_id}")

    # 6. Poll job status
    print(f"\n[TEST] GET /api/v1/jobs/{job_id} (polling)...")
    # Wait a moment for background task to execute
    import time
    time.sleep(2)
    response = client.get(f"/api/v1/jobs/{job_id}", headers={"X-API-Key": TEST_API_KEY})
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    print(f"[PASS] Job state is currently: {response.json()['data']['status']}")

    print("\n" + "="*60)
    print("ALL API V1 INTEGRATION TESTS COMPLETED SUCCESSFULLY")
    print("="*60)

if __name__ == "__main__":
    test_api_v1()
