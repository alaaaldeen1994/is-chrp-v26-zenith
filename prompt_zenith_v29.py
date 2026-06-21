import requests
import json
import sys

# Set output to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 70)
    print("ZENITH v29.0 PROMPT INTERFACE")
    print("2M Cell Foundation Model - Active Generative Discovery")
    print("=" * 70)
    
    # Get user prompt
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your reprogramming/aging prompt: ")
        
    cell_type = input("Enter target cell type (e.g. cardiac muscle cell, fibroblast): ")
    if not cell_type.strip():
        cell_type = "cardiac muscle cell"
        
    url = "http://127.0.0.1:9999/api/gpt-discovery/run"
    payload = {
        "query": query,
        "cell_type": cell_type
    }
    headers = {
        "Content-Type": "application/json"
    }

    print("\n[AI] Querying Zenith Foundation v29.0 (5858 Dimensions)...")
    try:
        response = requests.post(url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to the backend.")
        print("Please ensure `bridge_server.py` is running in another terminal window!")
        return

    if response.status_code == 200:
        data = response.json()
        
        print("\n" + "=" * 70)
        print("DISCOVERY RESULTS")
        print("=" * 70)
        print(f"Goal: {data.get('query')}")
        print(f"Target: {data.get('cell_type_label', cell_type)}")
        print(f"Age Delta: -{data.get('real_age_delta_years')} years")
        print(f"Method: {data.get('methodology')}")
        print("-" * 70)
        
        genes = data.get("genes", [])
        if not genes:
            print("No specific genes returned.")
        else:
            for idx, g in enumerate(genes, 1):
                direction = g.get('direction', 'UP')
                print(f" {idx}. {g.get('gene')} [{direction}] (score: {g.get('correlation')})")
                print(f"    Role: {g.get('role')}")
                print(f"    Mechanism: {g.get('mechanism')}")
                print()
                
    else:
        print(f"\nError {response.status_code}: {response.text}")

if __name__ == "__main__":
    main()
