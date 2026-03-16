import torch
import numpy as np
import json
import asyncio
from bridge_server import get_target_vector_from_query, get_drift_model, GENE_SYMBOLS

async def run_comparison():
    print("=== ZENITH V28 SCIENTIFIC AUDIT: HYBRID VS CANONICAL ===")
    
    # Test Cases
    tests = [
        {"query": "Induce pluripotency using Yamanaka factors", "expected": "OSKM"},
        {"query": "Differentiate into functional cardiomyocytes", "expected": "DIRECT_CARDIO"},
        {"query": "Create a cell that is both a neuron and a muscle cell", "expected": "UNCATEGORIZED PROTOCOL"}
    ]
    
    results = []
    
    for test in tests:
        print(f"\n[TEST] Query: '{test['query']}'")
        
        # 1. Semantic Mapping (LLM)
        target_vec, rationale, gene_data = await get_target_vector_from_query(test['query'])
        top_genes = list(gene_data.keys())
        print(f"  |-> LLM Mapping: {top_genes[:5]}... (Total: {len(top_genes)})")
        print(f"  |-> Rationale: {rationale}")
        
        # 2. Manifold Backprop (3B Model)
        current_vec = torch.zeros(1000) # Start from zero/null state
        perturbation = torch.zeros_like(current_vec, requires_grad=True)
        
        input_tensor = torch.cat([current_vec + perturbation, torch.tensor([0.5]), torch.zeros(1000)]).unsqueeze(0).to(torch.float16)
        velocity = get_drift_model()(input_tensor)
        velocity_genes = velocity[0, :1000].to(torch.float32)
        
        loss = torch.nn.functional.mse_loss(current_vec + velocity_genes, target_vec)
        loss.backward()
        gradient = perturbation.grad
        ideal_vector = -gradient.detach().numpy()
        
        # 3. Protocol Matching
        protocols = {
            'OSKM': [0, 1, 4, 5],
            'DIRECT_CARDIO': [13, 14, 15, 16],
        }
        
        match_scores = {}
        for name, indices in protocols.items():
            proto_vec = np.zeros(1000)
            for idx in indices: proto_vec[idx] = 1.0
            pos_ideal = np.maximum(ideal_vector, 0)
            score = np.dot(pos_ideal, proto_vec) / (np.linalg.norm(pos_ideal) * np.linalg.norm(proto_vec) + 1e-9)
            match_scores[name] = score

        best = max(match_scores, key=match_scores.get) if any(match_scores.values()) else "UNCATEGORIZED PROTOCOL"
        if match_scores.get(best, 0) < 0.05: best = "UNCATEGORIZED PROTOCOL"
        
        print(f"  |-> Identified Protocol: {best} (Confidence: {match_scores.get(best, 0):.2f})")
        
        results.append({
            "query": test['query'],
            "best": best,
            "match_scores": match_scores,
            "pass": (best == test['expected'])
        })

    print("\n=== FINAL AUDIT SUMMARY ===")
    for r in results:
        status = "PASSED" if r['pass'] else "FAILED"
        print(f"{status}: '{r['query']}' -> {r['best']}")

if __name__ == "__main__":
    asyncio.run(run_comparison())
