import requests
import json
import sys

# Set output to UTF-8 to prevent Windows terminal encoding errors
sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:9999/api/gpt-discovery/run"
payload = {
    "query": "Reprogram mural pericytes into functional capillary endothelial cells to restore blood flow and reduce microvascular leakage.",
    "cell_type": "pericyte"
}
headers = {
    "Content-Type": "application/json"
}

print("Sending request to /api/gpt-discovery/run...")
response = requests.post(url, json=payload, headers=headers)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    
    # Save the raw JSON data to scratch/pericyte_reprogramming_result.json
    out_file = "scratch/pericyte_reprogramming_result.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved full JSON output to: {out_file}")

    print("\n--- TOURNAMENT DISCOVERY RESULTS ---")
    print(f"Query: {data.get('query')}")
    print(f"Cell Type: {data.get('cell_type')} ({data.get('cell_type_label')})")
    print(f"Methodology: {data.get('methodology')}")
    print(f"Rounds Completed: {data.get('rounds_completed')}")
    print(f"Epigenetic Age Delta: -{data.get('real_age_delta_years')}y")
    print(f"Tournament Confidence: {data.get('tournament_confidence')*100}%")
    print(f"Judge Decision: {data.get('judge_reasoning')}")
    print(f"Refinement Notes: {data.get('refinement_notes')}\n")
    print("Genes returned:")
    for idx, g in enumerate(data.get("genes", []), 1):
        print(f"  {idx}. {g.get('gene')} (r={g.get('correlation')}, direction={g.get('direction')})")
        print(f"     Role: {g.get('role')}")
        print(f"     Mechanism: {g.get('mechanism')}")
        print(f"     PubMed: {g.get('pubmed_url')}")
        print()
else:
    print(response.text)
