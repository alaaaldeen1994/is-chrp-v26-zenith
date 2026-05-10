import requests
import json
import os
import time

# ZENITH v27.0 GOLD - UNIFIED HEALTH CHECK
# This script verifies the end-to-end D2B (Digital-to-Biological) pipeline.

BASE_URL = "http://localhost:9999"

def run_health_check():
    print("\n[ZENITH HEALTH CHECK] Initiating Global Integration Test...\n")
    
    # 1. Test Discovery + AF3 Bridge
    print("STEP 1: Testing AI Discovery + AlphaFold 3 Bridge...")
    discovery_payload = {
        "target_type": "CARDIO",
        "current_genes": [0.1] * 1000,
        "knockouts": [1, 2]
    }
    try:
        resp = requests.post(f"{BASE_URL}/discover_protocol", json=discovery_payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  > Success: Protocol '{data['recommended_protocol']}' discovered.")
            if data.get('af3_validation'):
                print(f"  > Success: AF3 Manifest generated: {data['af3_validation']['job_id']}")
            else:
                print("  ! Warning: AF3 validation data missing in response.")
        else:
            print(f"  ! Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"  ! Error: {e}")

    # 2. Test Dosage Optimization
    print("\nSTEP 2: Testing Bayesian Dosage Optimization...")
    try:
        resp = requests.post(f"{BASE_URL}/api/v2/dosage_optimization")
        if resp.status_code == 200:
            dosage_data = resp.json()
            print(f"  > Success: Optimal rhythm found: {dosage_data['optimal_on_hours']}h ON / {dosage_data['optimal_off_hours']}h OFF")
            
            # 3. Test Robotic Bridge (D2B)
            print("\nSTEP 3: Testing Robotic Synthesis Bridge (D2B)...")
            robot_payload = {
                "discovery_data": {
                    "target_query": "Cardiac Rejuvenation",
                    "recommended_protocol": "DIRECT_CARDIO",
                    "target_profile": {"GATA4": 1.0}
                },
                "dosage_audit": dosage_data
            }
            resp_robot = requests.post(f"{BASE_URL}/generate_opentrons_protocol", json=robot_payload)
            if resp_robot.status_code == 200:
                robot_data = resp_robot.json()
                print("  > Success: Opentrons Flex manifest generated.")
                if "metadata = {" in robot_data['script']:
                    print("  > Success: Script content verified (metadata found).")
            else:
                print(f"  ! Failed: {resp_robot.status_code}")
        else:
            print(f"  ! Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ! Error: {e}")

    print("\n[ZENITH HEALTH CHECK] Complete.\n")

if __name__ == "__main__":
    run_health_check()
