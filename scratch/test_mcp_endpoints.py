import subprocess
import json
import os
import sys

def run_mcp_cmd(input_json: dict) -> dict:
    env = os.environ.copy()
    env["ZENITH_API_KEY"] = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"
    env["ZENITH_API_URL"] = "http://127.0.0.1:9999/api/v1"
    
    # Run mcp_server.py in a subprocess, redirecting stdin and stdout
    proc = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    
    stdout_data, stderr_data = proc.communicate(input=json.dumps(input_json) + "\n")
    
    # Print debug logs from stderr if any
    for line in stderr_data.split("\n"):
        if line.strip():
            print(f"  [MCP LOG] {line}")
            
    # Parse output lines
    for line in stdout_data.split("\n"):
        if line.strip():
            return json.loads(line)
    return {}

def test_mcp():
    print("=" * 70)
    print("      ZENITH MCP SERVER - END-TO-END INTEGRATION TESTS")
    print("=" * 70)
    
    # 1. Test tools/list
    print("\n[STEP 1] Querying tools/list...")
    list_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    res = run_mcp_cmd(list_req)
    tools = res.get("result", {}).get("tools", [])
    print(f"  [OK] Returned {len(tools)} tools:")
    for t in tools:
        print(f"    - {t['name']}: {t['description'][:60]}...")
        
    # 2. Test tools/call: safety_audit
    print("\n[STEP 2] Calling safety_audit tool...")
    audit_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "safety_audit",
            "arguments": {
                "factors": ["GATA4", "MEF2C"]
            }
        }
    }
    res = run_mcp_cmd(audit_req)
    content = res.get("result", {}).get("content", [])
    if content:
        print("  [OK] Tool Call Output:")
        payload = json.loads(content[0]["text"])
        print(json.dumps(payload, indent=4))
    else:
        print("  [ERROR] No content in response:", res)

if __name__ == "__main__":
    test_mcp()
