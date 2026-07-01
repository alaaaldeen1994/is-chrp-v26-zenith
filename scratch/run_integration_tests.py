import sys
import os
import time
import json

# Reconfigure stdout stream to UTF-8 to handle unicode safely
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Add Python SDK to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sdks", "python"))

from zenith import ZenithClient
from zenith.exceptions import AuthenticationError, ValidationError, ZenithException

# Local backend URL & Test Key
BASE_URL = "http://127.0.0.1:9999/api/v1"
TEST_KEY = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"

def run_tests():
    print("=" * 70)
    print("      ZENITH PYTHON SDK - END-TO-END INTEGRATION TESTS")
    print("=" * 70)
    print(f"Target Server: {BASE_URL}")
    print(f"Auth Key:      {TEST_KEY[:10]}...")
    
    # 1. Initialize Client
    client = ZenithClient(api_key=TEST_KEY, base_url=BASE_URL)
    print("\n[STEP 1] Initialization: SUCCESS")
    
    # 2. Test Safety Audit (with CpG biological clock calculation)
    print("\n[STEP 2] Running Safety Audit tool...")
    t0 = time.time()
    try:
        audit = client.safety_audit(
            factors=["GATA4", "TBX5", "OCT4"],
            cpg_methylation={
                "cg00000292": 0.85,
                "cg00050873": 0.12,
                "cg00095927": 0.95,
                "cg02033393": 0.05
            }
        )
        latency = (time.time() - t0) * 1000
        print(f"  [OK] Latency: {latency:.1f} ms")
        print("  [OK] Approved factors:", audit.get("approved_factors"))
        print("  [OK] Blocked factors: ", audit.get("blocked_factors"))
        print("  [OK] Methylation age: ", audit.get("cpg_age_years"), "years")
    except Exception as e:
        print(f"  [ERROR] Failed Safety Audit: {e}")
        sys.exit(1)
        
    # 3. Test ESMFold Protein Folding
    print("\n[STEP 3] Running Protein Folding tool (ESMFold)...")
    t0 = time.time()
    try:
        fold = client.fold_sequence("MGDVEKGKKIFIMKCSQCHTVEKGGKHKTGPNLHGLFG")
        latency = (time.time() - t0) * 1000
        print(f"  [OK] Latency: {latency:.1f} ms")
        pdb_lines = fold.get("pdb_data", "").split("\n")
        print(f"  [OK] Returned PDB coordinates: {len(pdb_lines)} lines")
        print(f"  [OK] First PDB line: {pdb_lines[0] if pdb_lines else 'None'}")
    except Exception as e:
        print(f"  [ERROR] Failed ESMFold query: {e}")
        sys.exit(1)

    # 4. Test LNP Optimizer
    print("\n[STEP 4] Running LNP formulation optimization...")
    t0 = time.time()
    try:
        lnp = client.optimize_lnp(
            molar_ratios={"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
            np_ratio=6.0
        )
        latency = (time.time() - t0) * 1000
        print(f"  [OK] Latency: {latency:.1f} ms")
        print("  [OK] Encapsulation efficiency:", lnp.get("encapsulation_efficiency_percent"), "%")
        print("  [OK] Heart selectivity score: ", lnp.get("heart_selectivity_score"))
        print("  [OK] Cytotoxicity rating:     ", lnp.get("metrics", {}).get("cytotoxicity"))
    except Exception as e:
        print(f"  [ERROR] Failed LNP Optimizer: {e}")
        sys.exit(1)

    # 5. Test Async Perturbation Prediction
    print("\n[STEP 5] Running Async Transcriptomic Perturbation Forecasting...")
    t0 = time.time()
    try:
        # Note: We trigger async simulation by passing a census filter to start a background task
        pert = client.predict_perturbation(
            perturbation_factors={"GATA4": 1.5},
            baseline_cell_type="ventricular_myocyte",
            census_filter="tissue == 'heart'",
            poll=True,
            poll_interval=1.0
        )
        latency = (time.time() - t0) * 1000
        print(f"  [OK] Completed in: {latency/1000:.2f} s")
        print("  [OK] Final Status: ", pert.get("status"))
        print("  [OK] Cell types in output:", pert.get("result", {}).get("cell_count"))
        
        # Verify h5ad download
        job_id = pert.get("job_id")
        if job_id:
            h5ad_out = "scratch/temp_result.h5ad"
            print(f"  [OK] Downloading result AnnData matrix to {h5ad_out}...")
            client.download_result(job_id, h5ad_out)
            if os.path.exists(h5ad_out):
                print(f"  [OK] Download Success! File Size: {os.path.getsize(h5ad_out):,} bytes")
                os.remove(h5ad_out)
    except Exception as e:
        print(f"  [ERROR] Failed Perturbation: {e}")
        sys.exit(1)

    # 6. Verify Error Handling: Authentication
    print("\n[STEP 6] Verifying Authentication error handling...")
    try:
        bad_client = ZenithClient(api_key="zk_live_invalidkey", base_url=BASE_URL)
        bad_client.safety_audit(factors=["GATA4"])
        print("  [ERROR] FAIL: Authentication check did not raise AuthenticationError.")
        sys.exit(1)
    except AuthenticationError as e:
        print(f"  [PASS] Raised AuthenticationError: {e}")
    except Exception as e:
        print(f"  [ERROR] FAIL: Raised unexpected exception: {e}")
        sys.exit(1)

    # 7. Verify Error Handling: Validation
    print("\n[STEP 7] Verifying Request Validation error handling...")
    try:
        # Missing required molar_ratios or invalid keys
        client.optimize_lnp(molar_ratios={}, np_ratio=-5.0)
        print("  [ERROR] FAIL: Validation check did not raise ValidationError.")
        sys.exit(1)
    except ValidationError as e:
        print(f"  [PASS] Raised ValidationError: {e}")
    except Exception as e:
        print(f"  [ERROR] FAIL: Raised unexpected exception: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("   [SUCCESS] ALL PYTHON SDK INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
