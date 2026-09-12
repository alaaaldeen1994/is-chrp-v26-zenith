"""
Structure API Bridge for Nilus Lab / Zenith Platform (FastAPI)
Bridges /api/boltz, /api/alphafold, /api/pae, /api/references,
/api/compare, /api/interfaces, /api/qc, /api/ensemble
to the local scientific Node engine, with native Python fallback for Boltz on Railway.
"""

import os
import shutil
import subprocess
import asyncio
from typing import Optional, Dict, Any
import httpx
from fastapi import APIRouter, Request, Response, HTTPException

structure_router = APIRouter()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
NODE_URL = os.getenv("NODE_API_URL", "http://127.0.0.1:3001")
BOLTZ_BASE_URL = os.getenv("BOLTZ_API_BASE", "https://api.boltz.bio").rstrip("/")

_node_process: Optional[subprocess.Popen] = None


def get_boltz_api_key() -> str:
    key = os.getenv("BOLTZ_API_KEY", "").strip()
    if not key:
        # Check .env.local if running locally
        env_local = os.path.join(BASE_DIR, ".env.local")
        if os.path.exists(env_local):
            try:
                with open(env_local, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("BOLTZ_API_KEY="):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if key:
                                os.environ["BOLTZ_API_KEY"] = key
                                break
            except Exception:
                pass
    return key


def get_key_mode(key: str) -> str:
    if "_live_" in key:
        return "live"
    if "_test_" in key:
        return "test"
    return "unknown"


async def is_node_alive() -> bool:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            r = await client.get(f"{NODE_URL}/__nilus/health")
            return r.status_code == 200
    except Exception:
        return False


async def init_structure_node_worker():
    """Starts local node server if node is installed and server is not already running."""
    global _node_process
    if await is_node_alive():
        print(f"[STRUCTURE-BRIDGE] Node engine already active at {NODE_URL}")
        return

    node_bin = shutil.which("node")
    server_script = os.path.join(BASE_DIR, "tools", "local-dev-server.js")
    if node_bin and os.path.exists(server_script):
        try:
            print(f"[STRUCTURE-BRIDGE] Launching background Node server ({server_script})...")
            env = os.environ.copy()
            key = get_boltz_api_key()
            if key:
                env["BOLTZ_API_KEY"] = key
            _node_process = subprocess.Popen(
                [node_bin, server_script],
                cwd=BASE_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Wait briefly for startup
            for _ in range(10):
                await asyncio.sleep(0.3)
                if await is_node_alive():
                    print(f"[STRUCTURE-BRIDGE] Node engine online at {NODE_URL}")
                    return
            print("[STRUCTURE-BRIDGE] Node process launched; awaiting first health response.")
        except Exception as e:
            print(f"[STRUCTURE-BRIDGE] Failed to launch node process: {e}")
    else:
        print("[STRUCTURE-BRIDGE] Node runtime not present; operating in native Python bridge mode.")


async def shutdown_structure_node_worker():
    global _node_process
    if _node_process:
        print("[STRUCTURE-BRIDGE] Terminating background Node server...")
        try:
            _node_process.terminate()
            _node_process.wait(timeout=2.0)
        except Exception:
            _node_process.kill()
        _node_process = None


async def proxy_request(request: Request, path: str) -> Optional[Response]:
    """Proxies HTTP request to local Node server if available."""
    try:
        url = f"{NODE_URL}{path}"
        if request.url.query:
            url += f"?{request.url.query}"
        
        body = await request.body()
        headers = {}
        for h in ["content-type", "accept", "user-agent"]:
            v = request.headers.get(h)
            if v:
                headers[h] = v

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body if body else None,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
                headers={"cache-control": resp.headers.get("cache-control", "no-store")},
            )
    except Exception:
        return None


# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================

@structure_router.post("/api/boltz")
async def api_boltz(request: Request):
    # 1. Try forwarding to Node server
    proxied = await proxy_request(request, "/api/boltz")
    if proxied is not None:
        return proxied

    # 2. Native Python fallback
    key = get_boltz_api_key()
    if not key:
        return Response(
            content='{"error":"BOLTZ_API_KEY is not configured on the server."}',
            status_code=503,
            media_type="application/json"
        )

    try:
        body = await request.json()
    except Exception:
        return Response(content='{"error":"Invalid JSON body"}', status_code=400, media_type="application/json")

    action = body.get("action", "")
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": key,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        if action == "health":
            try:
                r = await client.get(f"{BOLTZ_BASE_URL}/compute/v1/auth/me", headers=headers, timeout=10.0)
                if r.status_code == 200:
                    return Response(
                        content=f'{{"configured":true,"authenticated":true,"mode":"{get_key_mode(key)}"}}',
                        status_code=200,
                        media_type="application/json"
                    )
                return Response(content=r.content, status_code=r.status_code, media_type="application/json")
            except Exception as e:
                return Response(content=f'{{"error":"Failed to reach Boltz: {str(e)}"}}', status_code=502, media_type="application/json")

        elif action == "estimate":
            req_data = body.get("request", {})
            r = await client.post(f"{BOLTZ_BASE_URL}/compute/v1/predictions/structure-and-binding/estimate-cost", headers=headers, json=req_data)
            return Response(content=r.content, status_code=r.status_code, media_type="application/json")

        elif action == "submit":
            req_data = body.get("request", {})
            r = await client.post(f"{BOLTZ_BASE_URL}/compute/v1/predictions/structure-and-binding", headers=headers, json=req_data)
            return Response(content=r.content, status_code=r.status_code, media_type="application/json")

        elif action == "status":
            pred_id = body.get("id", "")
            r = await client.get(f"{BOLTZ_BASE_URL}/compute/v1/predictions/structure-and-binding/{pred_id}", headers=headers)
            return Response(content=r.content, status_code=r.status_code, media_type="application/json")

        elif action == "structure":
            pred_id = body.get("id", "")
            r = await client.get(f"{BOLTZ_BASE_URL}/compute/v1/predictions/structure-and-binding/{pred_id}", headers=headers)
            if r.status_code != 200:
                return Response(content=r.content, status_code=r.status_code, media_type="application/json")
            pred = r.json()
            if pred.get("status") != "succeeded":
                return Response(content=f'{{"error":"Prediction status is {pred.get("status")}"}}', status_code=409, media_type="application/json")
            best = pred.get("output", {}).get("best_sample", {})
            art_url = best.get("structure", {}).get("url")
            if not art_url:
                return Response(content='{"error":"No structure URL available"}', status_code=404, media_type="application/json")
            art_res = await client.get(art_url, timeout=60.0)
            structure_text = art_res.text
            fmt = "pdb" if ".pdb" in art_url.lower() or structure_text.startswith("ATOM  ") else "cif"
            import json
            payload = {
                "result": pred,
                "structure": structure_text,
                "format": fmt,
                "metrics": best.get("metrics"),
                "sample_index": 0,
                "is_best_sample": True,
            }
            return Response(content=json.dumps(payload), status_code=200, media_type="application/json")

    return Response(content='{"error":"Unknown Boltz action"}', status_code=400, media_type="application/json")


@structure_router.get("/api/alphafold")
async def api_alphafold(request: Request):
    proxied = await proxy_request(request, "/api/alphafold")
    if proxied is not None:
        return proxied

    accession = request.query_params.get("accession", "").strip().upper()
    if not accession:
        return Response(content='{"error":"A valid UniProt accession is required."}', status_code=400, media_type="application/json")

    url = f"https://alphafold.ebi.ac.uk/api/prediction/{accession}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers={"accept": "application/json"})
            if r.status_code == 404:
                return Response(content='{"error":"No AlphaFold DB prediction found"}', status_code=404, media_type="application/json")
            if r.status_code != 200:
                return Response(content=f'{{"error":"AlphaFold DB returned {r.status_code}"}}', status_code=502, media_type="application/json")
            entries = r.json()
            entry = entries[0] if isinstance(entries, list) and entries else {}
            import json
            payload = {
                "accession": entry.get("uniprotAccession", accession),
                "entry_id": entry.get("entryId"),
                "tool": entry.get("toolUsed"),
                "sequence": entry.get("sequence"),
                "mean_plddt": entry.get("globalMetricValue"),
                "pdb_url": entry.get("pdbUrl"),
                "cif_url": entry.get("cifUrl"),
                "pae_url": entry.get("paeDocUrl"),
                "source_url": f"https://alphafold.ebi.ac.uk/entry/{entry.get('entryId')}" if entry.get("entryId") else None,
            }
            return Response(content=json.dumps(payload), status_code=200, media_type="application/json")
    except Exception as e:
        return Response(content=f'{{"error":"Unable to reach AlphaFold DB: {str(e)}"}}', status_code=502, media_type="application/json")


@structure_router.get("/api/references")
async def api_references(request: Request):
    proxied = await proxy_request(request, "/api/references")
    if proxied is not None:
        return proxied

    accession = request.query_params.get("accession", "").strip().upper()
    if not accession:
        return Response(content='{"error":"UniProt accession required"}', status_code=400, media_type="application/json")

    query = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                        "operator": "exact_match",
                        "value": accession
                    }
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name",
                        "operator": "exact_match",
                        "value": "UniProt"
                    }
                }
            ]
        },
        "return_type": "polymer_entity",
        "request_options": {"paginate": {"start": 0, "rows": 12}}
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post("https://search.rcsb.org/rcsbsearch/v2/query", json=query)
            if r.status_code == 200:
                data = r.json()
                ids = [x.get("identifier", "").split("_")[0].upper() for x in data.get("result_set", []) if x.get("identifier")]
                refs = [{"pdb_id": pid, "source_url": f"https://www.rcsb.org/structure/{pid}"} for pid in set(ids)]
                import json
                return Response(content=json.dumps({"accession": accession, "experimental_references": refs, "count": len(refs)}), status_code=200, media_type="application/json")
            return Response(content='{"accession":"' + accession + '","experimental_references":[],"count":0}', status_code=200, media_type="application/json")
    except Exception as e:
        return Response(content=f'{{"error":"Failed to search RCSB: {str(e)}"}}', status_code=502, media_type="application/json")


@structure_router.get("/api/pae")
async def api_pae(request: Request):
    proxied = await proxy_request(request, "/api/pae")
    if proxied is not None:
        return proxied
    return Response(content='{"available":false,"reason":"PAE extraction requires active Node analysis engine"}', status_code=200, media_type="application/json")


@structure_router.post("/api/compare")
async def api_compare(request: Request):
    proxied = await proxy_request(request, "/api/compare")
    if proxied is not None:
        return proxied
    return Response(content='{"error":"Structure comparison engine requires active Node worker"}', status_code=503, media_type="application/json")


@structure_router.post("/api/interfaces")
async def api_interfaces(request: Request):
    proxied = await proxy_request(request, "/api/interfaces")
    if proxied is not None:
        return proxied
    return Response(content='{"error":"Interface analysis requires active Node worker"}', status_code=503, media_type="application/json")


@structure_router.post("/api/qc")
async def api_qc(request: Request):
    proxied = await proxy_request(request, "/api/qc")
    if proxied is not None:
        return proxied
    return Response(content='{"error":"QC analysis requires active Node worker"}', status_code=503, media_type="application/json")


@structure_router.post("/api/ensemble")
async def api_ensemble(request: Request):
    proxied = await proxy_request(request, "/api/ensemble")
    if proxied is not None:
        return proxied
    return Response(content='{"error":"Ensemble analysis requires active Node worker"}', status_code=503, media_type="application/json")
