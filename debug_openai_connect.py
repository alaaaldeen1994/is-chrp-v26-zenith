
import os
import asyncio
import httpx
from openai import AsyncOpenAI

async def test_connect():
    print("--- DIAGNOSTIC START ---")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("âŒ OPENAI_API_KEY not found in environment")
    else:
        print(f"âœ… OPENAI_API_KEY found (len={len(key)})")

    print("1. Testing raw HTTP connection to api.openai.com...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.openai.com/v1/models", 
                                  headers={"Authorization": f"Bearer {key}"} if key else {})
            print(f"   Response Code: {resp.status_code}")
            if resp.status_code == 200:
                print("   âœ… HIT (Authenticated)")
            elif resp.status_code == 401:
                print("   âš ï¸ HIT (Auth Failed - Key invalid)")
            else:
                print(f"   âš ï¸ HIT (Other Status: {resp.status_code})")
    except Exception as e:
        print(f"   âŒ FAILED: {e}")

    print("\n2. Testing OpenAI SDK...")
    try:
        client = AsyncOpenAI(api_key=key if key else "sk-mock-key")
        # Just list models as a cheap test
        models = await client.models.list()
        print(f"   âœ… SDK Success: Found {len(models.data)} models")
    except Exception as e:
        print(f"   âŒ SDK FAILED: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_connect())
    except Exception as e:
        print(f"Fatal script error: {e}")
