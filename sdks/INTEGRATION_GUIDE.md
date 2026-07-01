# Nilus Lab Zenith — Developer Integration Handbook

This guide contains complete setup instructions for integrating the Zenith platform into standard editor tools, AI agent frameworks, and custom LLM interfaces.

---

## 1. Python SDK

### Installation
Install the SDK directly using pip:
```bash
pip install zenith-sdk
```

### Quickstart
Ensure your environment variable `ZENITH_API_KEY` is configured:
```python
import os
from zenith import ZenithClient

# Reads ZENITH_API_KEY from env
client = ZenithClient()

# Check safety
audit = client.safety_audit(factors=["GATA4", "OCT4"])
print("Approved:", audit["approved_factors"])
```

---

## 2. Editor Integrations (MCP)

Zenith exposes tools through the **Model Context Protocol (MCP)**. This enables AI editors to execute biophysical simulations and safety audits locally.

### 2.1 Claude Desktop
Open your Claude Desktop configuration file (located at `%APPDATA%\Claude\claude_desktop_config.json` on Windows) and append the following configuration:
```json
{
  "mcpServers": {
    "zenith-mcp-server": {
      "command": "py",
      "args": ["-3.11", "C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/mcp_server.py"],
      "env": {
        "ZENITH_API_KEY": "your_api_key_here",
        "ZENITH_API_URL": "https://niluslab.com/api/v1"
      }
    }
  }
}
```

### 2.2 Cursor
1. Go to **Settings > Features > MCP**.
2. Click **+ Add New MCP Server**.
3. Configure the following details:
   * **Name**: `zenith-mcp-server`
   * **Type**: `command`
   * **Command**: `py -3.11 C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/mcp_server.py`
4. Add environment variables:
   * `ZENITH_API_KEY`: your raw API key.
   * `ZENITH_API_URL`: `https://niluslab.com/api/v1`

### 2.3 VS Code (Cline / Roo Code)
If you use Cline or Roo Code inside VS Code, open the MCP configuration settings file:
```json
{
  "mcpServers": {
    "zenith-mcp-server": {
      "command": "py",
      "args": ["-3.11", "C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/mcp_server.py"],
      "env": {
        "ZENITH_API_KEY": "your_api_key_here",
        "ZENITH_API_URL": "https://niluslab.com/api/v1"
      }
    }
  }
}
```

---

## 3. ChatGPT & OpenAI GPT Actions

To configure a Custom GPT to query the Zenith API:
1. Go to your **GPT Builder Console** on OpenAI.
2. Under **Configure**, click **Create New Action**.
3. Under **Schema**, paste the contents of [`config/openai_gpt_schema.json`](file:///C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/config/openai_gpt_schema.json).
4. Under **Authentication**, select **API Key**, type `X-API-Key` as the header parameter name, paste your API Key, and save.

---

## 4. Agent Frameworks

### 4.1 LangChain
Wrap the Zenith Client calls as custom tools:
```python
from langchain_core.tools import tool
from zenith import ZenithClient

client = ZenithClient()

@tool
def safety_audit_tool(factors: list[str]) -> str:
    """Evaluates candidate reprogramming factors for safety checks."""
    res = client.safety_audit(factors=factors)
    return str(res)
```
*(Reference: [`config/langchain_examples.py`](file:///C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/config/langchain_examples.py))*

### 4.2 LlamaIndex
Wrap Zenith functions using `FunctionTool`:
```python
from llama_index.core.tools import FunctionTool
from zenith import ZenithClient

client = ZenithClient()

def safety_audit_fn(factors: list[str]) -> dict:
    """Safety checks for transcription factor inputs."""
    return client.safety_audit(factors=factors)

safety_tool = FunctionTool.from_defaults(fn=safety_audit_fn, name="safety_audit")
```
*(Reference: [`config/llamaindex_examples.py`](file:///C:/Users/alaaa/.gemini/antigravity/scratch/is-chrp-v26-generative/config/llamaindex_examples.py))*

---

## 5. Security & Best Practices

1. **API Key Safety**: Never hardcode your API key inside public code repositories. Use environment variables (`ZENITH_API_KEY`).
2. **Rate Limits**: Zenith enforces an API rate limit of 100 requests/hour per standard API Key. Ensure your script incorporates backoff delays when calling endpoints in loops.
3. **Webhook HMAC Signatures**: Always verify incoming webhook payloads by calculating the SHA-256 HMAC digest on the raw request body bytes using your client secret.
