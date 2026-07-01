"""Production smoke test suite — runs against https://www.niluslab.com"""
import urllib.request, json, ssl, time

ctx = ssl.create_default_context()
BASE = "https://www.niluslab.com/api/v1"
API_KEY = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"
results = []

def post(path, body, key=API_KEY):
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers)
    t0 = time.time()
    try:
        res = urllib.request.urlopen(req, timeout=30, context=ctx)
        elapsed = (time.time() - t0) * 1000
        return res.status, json.loads(res.read().decode()), elapsed
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - t0) * 1000
        body_text = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(body_text), elapsed
        except:
            return e.code, body_text[:200], elapsed

def get(path, key=API_KEY):
    headers = {}
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        res = urllib.request.urlopen(req, timeout=30, context=ctx)
        return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        return e.code, body_text[:200]

print("=" * 60)
print("  PRODUCTION SMOKE TESTS — https://www.niluslab.com")
print("=" * 60)
print()

# Test 1: Health
print("[TEST 1] GET /health (no auth required)")
code, body = get("/health", key=None)
status = "PASS" if code == 200 else "FAIL"
print(f"  [{status}] HTTP {code}")
results.append(("Health", status))

# Test 2: Safety Audit
print("[TEST 2] POST /safety/audit")
code, body, ms = post("/safety/audit", {"factors": ["GATA4", "OCT4", "TBX5"]})
status = "PASS" if code == 200 else "FAIL"
if isinstance(body, dict):
    d = body.get("data", body)
    approved = d.get("approved_factors", [])
    blocked = d.get("blocked_factors", [])
    blocked_genes = [b.get("gene", "") for b in blocked]
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | Approved: {approved} | Blocked: {blocked_genes}")
else:
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | Body: {body}")
results.append(("Safety Audit", status))

# Test 3: LNP Optimize
print("[TEST 3] POST /lnp/optimize")
code, body, ms = post("/lnp/optimize", {
    "molar_ratios": {"ionizable": 0.50, "helper": 0.10, "cholesterol": 0.385, "peg": 0.015},
    "np_ratio": 6.0
})
status = "PASS" if code == 200 else "FAIL"
if isinstance(body, dict):
    d = body.get("data", body)
    eff = d.get("encapsulation_efficiency", "N/A")
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | Efficiency: {eff}")
else:
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | Body: {body}")
results.append(("LNP Optimize", status))

# Test 4: Protein Folding
print("[TEST 4] POST /structure/fold")
code, body, ms = post("/structure/fold", {"sequence": "MKFLILLFNILCLFPVLAENQDKI"})
status = "PASS" if code == 200 else "FAIL"
if isinstance(body, dict):
    d = body.get("data", body)
    pdb_text = d.get("pdb", "")
    pdb_lines = len(pdb_text.split("\n")) if pdb_text else 0
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | PDB lines: {pdb_lines}")
else:
    print(f"  [{status}] HTTP {code} | {ms:.0f}ms | Body: {body}")
results.append(("Protein Folding", status))

# Test 5: Auth rejection (no key)
print("[TEST 5] POST /safety/audit (NO API KEY)")
code, body, ms = post("/safety/audit", {"factors": ["GATA4"]}, key=None)
status = "PASS" if code == 401 else "FAIL"
print(f"  [{status}] HTTP {code} (expected 401) | {ms:.0f}ms")
results.append(("Auth No Key", status))

# Test 6: Auth rejection (invalid key)
print("[TEST 6] POST /safety/audit (INVALID KEY)")
code, body, ms = post("/safety/audit", {"factors": ["GATA4"]}, key="zk_live_invalidkey")
status = "PASS" if code == 401 else "FAIL"
print(f"  [{status}] HTTP {code} (expected 401) | {ms:.0f}ms")
results.append(("Auth Invalid Key", status))

# Test 7: Validation rejection
print("[TEST 7] POST /lnp/optimize (INVALID np_ratio=-5)")
code, body, ms = post("/lnp/optimize", {"np_ratio": -5.0})
status = "PASS" if code == 422 else "FAIL"
print(f"  [{status}] HTTP {code} (expected 422) | {ms:.0f}ms")
results.append(("Validation", status))

print()
print("=" * 60)
passed = sum(1 for _, s in results if s == "PASS")
total = len(results)
print(f"  RESULTS: {passed}/{total} PASSED")
for name, s in results:
    print(f"    [{s}] {name}")
if passed == total:
    print()
    print("  [SUCCESS] ALL PRODUCTION SMOKE TESTS PASSED!")
else:
    print()
    failed = [name for name, s in results if s != "PASS"]
    print(f"  [FAILURE] Failed: {failed}")
print("=" * 60)
