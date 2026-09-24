import urllib.request
import json
import time
import ssl

ctx = ssl.create_default_context()

BASE_URL = "https://www.niluslab.com"

endpoints = [
    ("Health", "GET", "/health", None),
    ("CSRF Token", "GET", "/api/csrf-token", None),
    ("Cell Types", "GET", "/api/cell-types", None),
    ("Cell Centroids", "GET", "/api/v2/centroids", None),
    ("Literature Audit", "GET", "/api/v2/literature-audit", None),
    ("Live Cells", "GET", "/api/cells/live", None),
    ("Real Discovery Run", "POST", "/api/real-discovery/run", {"cell_type": "Cardiomyocyte"}),
    ("Dosage Optimization", "POST", "/api/v2/dosage_optimization", {"target_reduction": 12.0}),
    ("Robotics Opentrons", "POST", "/api/v2/robotics/opentrons", {"protocol": "transient_pulse", "factors": ["GATA4", "MEF2C", "TBX5"]}),
    ("LNP Calculate", "POST", "/api/v2/lnp/calculate", {"factors": ["GATA4", "MEF2C", "TBX5"], "target_tissue": "heart"}),
    ("Virtual Trial", "POST", "/run_virtual_trial", {"disease": "Dilated Cardiomyopathy", "protocol": "DRP-Cardio-01", "cohort_size": 200, "variance": "High"}),
    ("Opentrons Protocol", "POST", "/generate_opentrons_protocol", {"discovery_data": {"target_query": "Dilated Cardiomyopathy", "cell_type": "Cardiomyocyte"}}),
    ("Boltz Health", "POST", "/api/boltz", {"action": "health"}),
    ("Wetlab Manifest", "POST", "/api/v2/generate-manifest", {"name": "CARDIAC_TEST", "factors": ["GATA4", "MEF2C", "TBX5"], "drugs": ["Rapamycin"], "target": "Cardiomyocyte"}),
    ("Vision Image Analyze", "POST", "/api/analyze_image", {"image_b64": "data:image/jpeg;base64,dGVzdA=="}),
    ("Structure Fold Alias", "POST", "/structure/fold", {"sequence": "MKTIIALSYIFCLVFA"}),
    ("AlphaGenome Variant Audit", "POST", "/api/v2/alphagenome/variant-audit", {"variant": "chr12:111,842,901 C>T", "gene_target": "MYH6", "disease_context": "Cardiomyopathy"}),
]

print("=" * 75)
print("TESTING PRODUCTION DEPLOYMENT AT", BASE_URL)
print("=" * 75)

passed = 0
failed = 0

for name, method, path, payload in endpoints:
    url = BASE_URL + path
    headers = {"User-Agent": "Mozilla/5.0"}
    data = None
    if method == "POST":
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            dt = (time.time() - t0) * 1000
            status = response.status
            body = response.read().decode("utf-8", errors="ignore")
            if status in (200, 201, 202):
                passed += 1
                print(f"[PASS] {status} ({dt:6.1f}ms) {name:28} -> {path}")
            else:
                failed += 1
                print(f"[FAIL] {status} ({dt:6.1f}ms) {name:28} -> {path} | Body: {body[:100]}")
    except urllib.error.HTTPError as e:
        dt = (time.time() - t0) * 1000
        body = e.read().decode("utf-8", errors="ignore")
        failed += 1
        print(f"[FAIL] {e.code} ({dt:6.1f}ms) {name:28} -> {path} | Body: {body[:100]}")
    except Exception as e:
        dt = (time.time() - t0) * 1000
        failed += 1
        print(f"[ERR ] ({dt:6.1f}ms) {name:28} -> {path} | Error: {e}")

print("=" * 75)
print(f"PRODUCTION SUMMARY: {passed} PASSED, {failed} FAILED")
print("=" * 75)
