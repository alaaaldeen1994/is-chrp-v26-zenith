import sys
import os
import json
import time
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bridge_server import app

client = TestClient(app)

# Use the test key generated during setup
TEST_API_KEY = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"

def test_api_v1():
    print("="*60)
    print("RUNNING API V1 SYSTEM INTEGRATION TESTS (PHASE 2)")
    print("="*60)

    # 1. Test Health endpoint (unauthenticated)
    print("\n[TEST] GET /api/v1/health...")
    response = client.get("/api/v1/health")
    print("Status:", response.status_code)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "online"

    # 2. Test LNP Optimize endpoint (authenticated)
    print("\n[TEST] POST /api/v1/lnp/optimize...")
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
    assert response.status_code == 200
    assert "circulation_half_life_hours" in response.json()["data"]
    assert "particle_size_nm" in response.json()["data"]
    print("[PASS] LNP Optimizations and nested metrics verified.")

    # 3. Test Horvath 353-CpG Epigenetic Clock calculations
    print("\n[TEST] POST /api/v1/safety/audit (with CpG methylation map)...")
    response = client.post(
        "/api/v1/safety/audit",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "factors": ["GATA4", "OCT4"],
            "cpg_methylation": {
                "cg00000292": 0.85,
                "cg00050873": 0.12,
                "cg00095927": 0.95,
                "cg02033393": 0.05
            }
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 200
    clock_impact = response.json()["data"]["horvath_clock_impact"]
    assert "predicted_biological_age" in clock_impact
    assert clock_impact["probes_matched"] == 4
    assert clock_impact["total_clock_probes"] == 353
    print(f"[PASS] Predicted biological age: {clock_impact['predicted_biological_age']} years")

    # 4. Test ESMFold 3D protein folding coordinate prediction
    print("\n[TEST] POST /api/v1/structure/fold (ESMFold)...")
    response = client.post(
        "/api/v1/structure/fold",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "sequence": "MGDSELEKKA"
        }
    )
    print("Status:", response.status_code)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "success"
    assert "ATOM " in data["pdb_data"]
    assert "END" in data["pdb_data"]
    print(f"[PASS] ESMFold folded structure returned (Source: {data['source']})")

    # 5. Test Asynchronous Cellxgene Census Perturbation & AnnData (.h5ad) serialization
    print("\n[TEST] POST /api/v1/predict/perturbation (Cellxgene filter -> async h5ad)...")
    response = client.post(
        "/api/v1/predict/perturbation",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "baseline_cell_type": "ventricular_myocyte",
            "perturbation_factors": {"GATA4": 1.5, "SIRT1": 2.0},
            "census_filter": "tissue_general == 'heart' and disease == 'normal'"
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    download_url = f"/api/v1/jobs/{job_id}/download"
    
    # Wait for the background task to complete cell query and AnnData write
    print("Polling job state for completion...")
    for _ in range(15):
        time.sleep(1)
        job_check = client.get(f"/api/v1/jobs/{job_id}", headers={"X-API-Key": TEST_API_KEY})
        status = job_check.json()["data"]["status"]
        print(f"  Job {job_id} status: {status}")
        if status == "completed":
            break
        elif status == "failed":
            raise AssertionError(f"Job failed: {job_check.json()['data'].get('error')}")
            
    assert status == "completed"
    print("[PASS] Background perturbation job finished successfully.")

    # 6. Test AnnData (.h5ad) binary download
    print(f"\n[TEST] GET {download_url} (downloading .h5ad)...")
    download_response = client.get(download_url, headers={"X-API-Key": TEST_API_KEY})
    print("Status:", download_response.status_code)
    print("Content Type:", download_response.headers.get("content-type"))
    print("Content Size:", len(download_response.content), "bytes")
    assert download_response.status_code == 200
    assert download_response.headers.get("content-type") == "application/octet-stream"
    assert len(download_response.content) > 1000 # Should be a valid binary file
    
    # Check if the download file is readable by AnnData locally
    temp_download = "scratch/temp_download.h5ad"
    with open(temp_download, "wb") as f:
        f.write(download_response.content)
        
    try:
        import anndata as ad
        adata = ad.read_h5ad(temp_download)
        print(f"Read AnnData success! Shape: {adata.shape}")
        assert adata.shape[0] == 50 # max_cells limit
        assert adata.shape[1] == len(adata.var_names)
        print("[PASS] Downloaded .h5ad file validated as fully readable and correctly shaped.")
    finally:
        if os.path.exists(temp_download):
            os.remove(temp_download)

    # 7. Test Webhook subscription and dispatching
    print("\n[TEST] POST /api/v1/webhooks/subscribe...")
    webhook_url = "https://mock.zenith.endpoint/webhook-callback"
    response = client.post(
        "/api/v1/webhooks/subscribe",
        headers={"X-API-Key": TEST_API_KEY},
        json={"url": webhook_url}
    )
    print("Status:", response.status_code)
    assert response.status_code == 200
    sub_data = response.json()["data"]
    assert "subscription_id" in sub_data
    assert "signing_secret" in sub_data
    assert sub_data["url"] == webhook_url
    print("[PASS] Webhook subscription registered successfully.")

    # We mock httpx.Client.post to check if webhook was dispatched
    from unittest.mock import MagicMock
    import httpx
    
    original_post = httpx.Client.post
    mock_post = MagicMock()
    
    def side_effect(self, url, *args, **kwargs):
        if "mock.zenith.endpoint" in str(url):
            mock_post(url, *args, **kwargs)
            return httpx.Response(200, json={})
        return original_post(self, url, *args, **kwargs)
        
    httpx.Client.post = side_effect
    
    try:
        # Trigger an async perturbation job, which will trigger a webhook on completion
        response = client.post(
            "/api/v1/predict/perturbation",
            headers={"X-API-Key": TEST_API_KEY},
            json={
                "baseline_cell_type": "ventricular_myocyte",
                "perturbation_factors": {"GATA4": 1.0},
                "census_filter": "tissue_general == 'heart'"
            }
        )
        print("Webhook test async perturbation response status:", response.status_code)
        print("Webhook test async perturbation response body:", response.json())
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        # Poll for completion
        for _ in range(15):
            time.sleep(1)
            job_check = client.get(f"/api/v1/jobs/{job_id}", headers={"X-API-Key": TEST_API_KEY})
            if job_check.json()["data"]["status"] == "completed":
                break
        
        # Verify that mock_post was called with the webhook
        # Since it runs in a background thread, let's wait a small amount for the thread to fire
        time.sleep(2)
        assert mock_post.called
        # Check call arguments
        called_url = mock_post.call_args[0][0]
        assert called_url == webhook_url
        
        # Check headers or signature
        headers = mock_post.call_args[1].get("headers", {})
        assert "X-Zenith-Signature" in headers
        assert "X-Zenith-Subscription-ID" in headers
        print("[PASS] Webhook dispatcher signature and payload validation complete.")
    finally:
        httpx.Client.post = original_post

    print("\n" + "="*60)
    print("ALL PHASE 2 API SCIENTIFIC UPGRADE TESTS PASSED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    test_api_v1()
