import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from bridge_server import app

def test_genes():
    client = TestClient(app)
    response = client.get("/api/v1/reference/genes", headers={"X-API-Key": "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"})
    print("Response Status Code:", response.status_code)
    data = response.json()
    print("Response Total Genes:", data["data"]["total"])
    print("First 10 genes:", data["data"]["genes"][:10])
    assert response.status_code == 200
    assert data["data"]["total"] == 4908
    print("SUCCESS: Gene count matches 4908!")

if __name__ == "__main__":
    test_genes()
