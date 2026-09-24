import sys
import os

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient

try:
    import bridge_server
    app = bridge_server.app
    client = TestClient(app)
    
    test_urls = [
        "/",
        "/index.html",
        "/partial-reprogramming",
        "/af3_jobs/",
        "/discovery.html",
        "/discovery",
        "/colony_microscopy_demo.html",
        "/evidence.html",
        "/evidence",
        "/regulatory.html",
        "/regulatory",
        "/api/cell-types",
        "/api/v2/dosage_optimization",
        "/run_virtual_trial",
        "/api/gpt-discovery/run",
        "/generate_opentrons_protocol",
        "/profile.html",
        "/profile",
        "/trials.html",
        "/trials",
        "/whitepaper.html",
        "/whitepaper",
        "/technical_catalog.html",
        "/robots.txt",
        "/sitemap.xml"
    ]
    
    print("Testing GET requests on all GSC URLs:")
    for url in test_urls:
        try:
            res = client.get(url, follow_redirects=False)
            print(f"GET {url:35} -> Status: {res.status_code}")
        except Exception as e:
            print(f"GET {url:35} -> ERROR: {e}")

except Exception as e:
    import traceback
    traceback.print_exc()
