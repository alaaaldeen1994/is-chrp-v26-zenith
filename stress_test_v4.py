import asyncio
import aiohttp
import time
import psutil
import os
import numpy as np

# Configuration
URL = "http://127.0.0.1:9995"
CONCURRENT_REQUESTS = 10 # Simulate simultaneous researchers
TOTAL_REQUESTS = 60

async def send_impute_request(session, req_id):
    """Simulates a researcher pushing a cell through the manifold"""
    payload = {
        "genes": np.random.normal(0.5, 0.1, 100).tolist() # Just the first 100 genes for the request
    }
    
    start_time = time.time()
    try:
        # Note: In a real environment we'd need the X-API-Key, 
        # but for this local stress test we are testing the computational logic.
        async with session.post(f"{URL}/impute", json=payload, headers={"X-API-Key": "ZENITH_ULTRA_PHASE4_KEY"}) as resp:
            status = resp.status
            latency = time.time() - start_time
            if status == 200:
                data = await resp.json()
                return {
                    "id": req_id,
                    "status": status,
                    "latency": latency,
                    "esi": data.get("epigenetic_stability_index", 0)
                }
            else:
                body = await resp.text()
                return {"id": req_id, "status": status, "latency": latency, "error": body}
    except Exception as e:
        return {"id": req_id, "status": "error", "latency": 0, "error": str(e)}

async def main():
    print("==================================================================")
    print("STRESS TEST: ZENITH ULTRA-V4 PRODUCTION SCALE")
    print("==================================================================")
    print(f"Target: {URL}")
    print(f"Concurrency: {CONCURRENT_REQUESTS} Simultaneous Maneuvers")
    print("------------------------------------------------------------------")

    # Start the server in the background if needed? 
    # Actually, I will assume the user or the environment has it ready, 
    # but I'll check if it's up.
    
    async with aiohttp.ClientSession() as session:
        # Check health first
        try:
            async with session.get(f"{URL}/health") as resp:
                health = await resp.json()
                print(f"SYSTEM HEALTH: {health['status']} | ENGINE: {health['engine']}")
        except:
            print("ERROR: Backend server not detected at 127.0.0.1:9997")
            print("Please ensure 'python bridge_server.py' is running.")
            return

        print("\nSTOCHASTIC BURST STARTING...")
        
        start_burst = time.time()
        tasks = []
        for i in range(TOTAL_REQUESTS):
            tasks.append(send_impute_request(session, i))
            
        # Run in chunks to simulate concurrent load
        results = []
        for i in range(0, len(tasks), CONCURRENT_REQUESTS):
            chunk = tasks[i:i+CONCURRENT_REQUESTS]
            chunk_results = await asyncio.gather(*chunk)
            results.extend(chunk_results)
            
            # Log memory after each chunk
            mem = psutil.virtual_memory()
            print(f"  [CHUNK {i//CONCURRENT_REQUESTS + 1}] Mem: {mem.percent}% | Avg Latency: {np.mean([r.get('latency', 0) for r in chunk_results]):.3f}s")

        total_time = time.time() - start_burst
        
        # Statistics
        success_results = [r for r in results if r["status"] == 200]
        latencies = [r["latency"] for r in success_results]
        success_rate = len(success_results) / TOTAL_REQUESTS * 100
        avg_esi = np.mean([r["esi"] for r in success_results]) if success_results else 0

        print("\n------------------------------------------------------------------")
        print("STRESS TEST SUMMARY")
        print("------------------------------------------------------------------")
        print(f"Total Requests: {TOTAL_REQUESTS}")
        print(f"Success Rate:   {success_rate:.1f}%")
        if latencies:
            print(f"Average Latency: {np.mean(latencies):.3f}s")
            print(f"Peak Latency:    {np.max(latencies):.3f}s")
        else:
            print("Average Latency: N/A")
        print(f"Manifold Stability (Avg ESI): {avg_esi*100:.2f}%")
        print(f"Total Burst Time: {total_time:.2f}s")
        
        if not success_results:
            print("\nALL REQUESTS FAILED. Sample Error:")
            print(f"  Status {results[0]['status']}: {results[0].get('error', 'Unknown Error')}")
        print("------------------------------------------------------------------")
        
        if success_rate > 95 and np.mean(latencies) < 0.5:
            print("TEST PASSED: Zenith Ultra is Production Ready.")
        else:
            print("TEST ADVISORY: Latency or Error rate exceeds clinical thresholds.")

    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(main())
