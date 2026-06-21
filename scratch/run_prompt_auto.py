import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    url = "http://127.0.0.1:9999/api/gpt-discovery/run"
    payload = {
        "query": "Find genes that use for aging like the GMT but from new training model",
        "cell_type": "cardiac muscle cell"
    }
    headers = {"Content-Type": "application/json"}

    print("\n[AI] Querying Zenith Foundation v29.0 API...")
    try:
        response = requests.post(url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to the backend. bridge_server.py is not running.")
        return

    if response.status_code == 200:
        data = response.json()
        print("\n--- RESULTS ---")
        genes = data.get("genes", [])
        if not genes:
            print("No genes found.")
        for idx, g in enumerate(genes, 1):
            print(f"{idx}. {g.get('gene')} (score: {g.get('correlation')})")
            print(f"   Role: {g.get('role')}")
            
        # Write results to a json file to be injected into the UI later
        with open("scratch/real_v29_prompt_results.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    main()
