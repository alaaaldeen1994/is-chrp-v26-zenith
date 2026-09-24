import urllib.request
import urllib.error
import ssl
import json

urls_to_test = [
    ("GET", "https://www.niluslab.com/"),
    ("GET", "https://www.niluslab.com/index.html"),
    ("GET", "https://www.niluslab.com/discovery.html"),
    ("GET", "https://www.niluslab.com/colony_microscopy_demo.html"),
    ("GET", "https://www.niluslab.com/evidence.html"),
    ("GET", "https://www.niluslab.com/regulatory.html"),
    ("GET", "https://www.niluslab.com/robots.txt"),
    ("GET", "https://www.niluslab.com/sitemap.xml"),
    # API endpoints (GET vs POST)
    ("GET", "https://www.niluslab.com/partial-reprogramming"),
    ("POST", "https://www.niluslab.com/partial-reprogramming", {}),
    ("GET", "https://www.niluslab.com/api/v2/dosage_optimization"),
    ("POST", "https://www.niluslab.com/api/v2/dosage_optimization", {}),
    ("GET", "https://www.niluslab.com/run_virtual_trial"),
    ("POST", "https://www.niluslab.com/run_virtual_trial", {}),
    ("GET", "https://www.niluslab.com/api/gpt-discovery/run"),
    ("POST", "https://www.niluslab.com/api/gpt-discovery/run", {"prompt": "test"}),
    ("GET", "https://www.niluslab.com/generate_opentrons_protocol"),
    ("POST", "https://www.niluslab.com/generate_opentrons_protocol", {}),
    ("GET", "https://www.niluslab.com/af3_jobs/"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

results = []
for item in urls_to_test:
    method = item[0]
    url = item[1]
    data = item[2] if len(item) > 2 else None
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    body = None
    if method == "POST":
        headers["Content-Type"] = "application/json"
        body = json.dumps(data or {}).encode('utf-8')
        
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            results.append((method, url, status, content_type, "OK"))
    except urllib.error.HTTPError as e:
        results.append((method, url, e.code, e.headers.get("Content-Type", ""), f"HTTPError: {e.reason}"))
    except Exception as e:
        results.append((method, url, 0, "", f"Error: {str(e)}"))

for method, url, status, ctype, msg in results:
    print(f"[{method}] {url} -> Status: {status} ({msg}) | Content-Type: {ctype}")
