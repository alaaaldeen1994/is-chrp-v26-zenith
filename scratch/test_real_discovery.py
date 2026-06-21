import json
import asyncio
from bridge_server import run_real_discovery

class FakeRequest:
    async def json(self):
        return {"cell_type": "fibroblast", "top_n": 10}

async def main():
    res = await run_real_discovery(FakeRequest())
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
