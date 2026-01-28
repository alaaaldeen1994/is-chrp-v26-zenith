
import requests
import json
import sys

# The domain seen in your screenshot
URL = "https://www.niluslab.com"

def check_status():
    print(f"🔍 Checking Status of {URL}...\n")
    
    # 1. Check Health / Mode
    try:
        r = requests.get(f"{URL}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            mode = data.get("mode", "UNKNOWN")
            print(f"✅ Server is ONLINE")
            print(f"📊 MODE: {mode}")
            
            if mode == "CLINICAL":
                print("   🌟 PASS: System is running in CLINICAL mode (Real Data Loaded).")
            elif mode == "PREVIEW":
                print("   ⚠️ WARNING: System is in PREVIEW mode (Mock Data). files might still be loading or crashed.")
            else:
                print(f"   ❓ STATUS: {mode}")
        else:
            print(f"❌ Error: Server returned status {r.status_code}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

    print("-" * 30)

    # 2. Check OpenAI / AI Connection
    try:
        r = requests.get(f"{URL}/test_openai", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"🤖 AI Connectivity:")
            print(f"   - API Key Set: {data.get('api_key_set')}")
            print(f"   - OpenAI Reachable: {data.get('openai_reachable')}")
            
            if data.get('openai_reachable'):
                print("   🌟 PASS: AI Brain is fully connected.")
            else:
                print("   ⚠️ FAIL: AI Brain is offline (using Fallback).")
    except:
        print("   ⚠️ Could not verify AI connection endpoint.")

if __name__ == "__main__":
    check_status()
