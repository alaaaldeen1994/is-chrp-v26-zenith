import json
import sys
import os
import io
import pytest
import respx
import httpx

# Add root folder to sys.path to import mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import mcp_server

@respx.mock
def test_mcp_tool_calls_safety_audit(monkeypatch):
    # Set mock environment variables
    monkeypatch.setenv("ZENITH_API_KEY", "test_api_key")
    monkeypatch.setenv("ZENITH_API_URL", "https://api.zenith-test.com/v1")

    # Mock the REST API call
    route = respx.post("https://api.zenith-test.com/v1/safety/audit").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "success",
                "data": {
                    "approved_factors": ["GATA4"],
                    "blocked_factors": ["MYC"],
                    "safety_summary": "Warning: Blocked factors."
                },
                "meta": {"credits_used": 1}
            }
        )
    )

    # Initialize the server
    server = mcp_server.ZenithMCPServer()

    # Capture stdout and stderr
    mock_stdout = io.StringIO()
    monkeypatch.setattr(sys.stdout, "write", mock_stdout.write)
    monkeypatch.setattr(sys.stdout, "flush", lambda: None)

    # Run the handler for a safety_audit tool call request
    tool_call_req = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "tools/call",
        "params": {
            "name": "safety_audit",
            "arguments": {
                "factors": ["GATA4", "MYC"]
            }
        }
    }
    
    server.handle_request(tool_call_req)
    assert route.called

    # Parse stdout response
    mock_stdout.seek(0)
    response_line = mock_stdout.read().strip()
    response = json.loads(response_line)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 42
    result = response["result"]
    assert len(result["content"]) == 1
    content_text = result["content"][0]["text"]
    tool_result = json.loads(content_text)
    
    assert tool_result["approved_factors"] == ["GATA4"]
    assert tool_result["blocked_factors"] == ["MYC"]
