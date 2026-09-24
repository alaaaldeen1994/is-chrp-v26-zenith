import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath("."))
import bridge_server
from bridge_server import app

client = TestClient(app)

def get_all_routes(app):
    routes = []
    def extract_routes(app_or_router, prefix=""):
        for route in getattr(app_or_router, "routes", []):
            if hasattr(route, "path_format"):
                routes.append((list(getattr(route, "methods", ["GET"])), prefix + route.path_format))
            elif hasattr(route, "path"):
                routes.append((list(getattr(route, "methods", ["GET"])), prefix + route.path))
            if hasattr(route, "app") and hasattr(route.app, "routes"):
                extract_routes(route.app, prefix=route.path)
            elif hasattr(route, "routes"):
                extract_routes(route, prefix=getattr(route, "prefix", ""))
    extract_routes(app)
    return routes

all_routes = get_all_routes(app)
print(f"Total routes extracted properly: {len(all_routes)}")

# Filter for key endpoints
print("\n--- Key endpoints found in app: ---")
for methods, path in sorted(all_routes, key=lambda x: x[1]):
    if any(k in path for k in ['discovery', 'dosage', 'boltz', 'trial', 'perturbation', 'reprogramming', 'opentrons', 'lnp', 'neural', 'centroids', 'manifest', 'literature']):
        print(f"{methods} {path}")

