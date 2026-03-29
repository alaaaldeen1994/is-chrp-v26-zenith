"""
zenith_discovery_pipeline.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
IS-v26.1 - FULL INSTITUTIONAL DISCOVERY WORKFLOW (Hybrid Intuition Edition).
[Scientific Prompt] -> [Zenith-AI Parsing] -> [UniProt JSON] -> [PTM Mapping] -> [DHL Refinement] -> [AF3 Manifest]

Author: Antigravity AI
Date: 2026-03-29
"""

import os
import sys
import json
import time
import requests
import re
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load credentials
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ZenithDiscoveryEngine:
    """Zenith v26.1 Senior Institutional Engine (Hybrid Intuition Edition)."""
    
    def __init__(self):
        self.institutional_seed = 2142086823
        self.z_pillar_dna = "CCTGTGACTGTGGGGTTCACGCTCCCGGGTG" # 31bp
        self.linker_extension = 15
        
        # Hardcoded Accession Registry
        self.uniprot_registry = {
            "SOX2": "P48431",
            "OCT4": "Q01860",
            "POU5F1": "Q01860"
        }
        
        # Hardcoded Domain Knowledge
        self.isl = {
            "GATA4": {"s": 212, "e": 332, "fam": "Zinc-Finger"},
            "NKX2.5": {"s": 138, "e": 203, "fam": "Homeodomain"},
            "TBX5": {"s": 70, "e": 352, "fam": "T-box"},
            "SNAI1": {"s": 151, "e": 240, "fam": "Zinc-Finger"},
            "TWIST1": {"s": 109, "e": 164, "fam": "bHLH"},
            "SOX2": {"s": 38, "e": 120, "fam": "HMG-box"},
            "OCT4": {"s": 133, "e": 288, "fam": "POU-domain"},
            "KLF4": {"s": 390, "e": 483, "fam": "Zinc-Finger"}
        }

    # ============================================================
    # STAGE 0: PROMPT INTERPRETATION
    # ============================================================
    def parse_factors_from_prompt(self, prompt: str) -> List[str]:
        """Uses Zenith-AI (OpenAI) to extract target protein symbols."""
        print(f"🧬 Stage 0: Zenith-AI parsing scientific intent...")
        try:
            ai_prompt = (
                "Identify the top 5 Human gene symbols (e.g. PPARGC1A, HCN4) "
                "from this objective: '" + prompt + "'. Return ONLY a comma-separated list."
            )
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": ai_prompt}],
                max_tokens=30,
                temperature=0.0
            )
            symbols = response.choices[0].message.content.strip().replace(" ", "").split(",")
            return [s.upper() for s in symbols if s]
        except Exception as e:
            print(f"  ❌ AI Parsing Error: {e}")
            return []

    # ============================================================
    # STAGE 2: ZENITH-AI (OPENAI ID MAPPING)
    # ============================================================
    def map_to_uniprot_accession(self, factor_symbol: str) -> Optional[str]:
        """Uses AI to identify the correct UniProt Accession."""
        if factor_symbol in self.uniprot_registry:
            return self.uniprot_registry[factor_symbol]
            
        print(f"🧠 Stage 2: Mapping '{factor_symbol}' to UniProt Accession...")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Human UniProt Accession for gene {factor_symbol}. Return only the ID (e.g. P48431)."}],
                max_tokens=20,
                temperature=0.0
            )
            accession = response.choices[0].message.content.strip()
            # Clean up potential markdown or junk
            accession = re.search(r"([A-Z0-9]{6,10})", accession)
            if accession:
                return accession.group(1)
        except Exception as e:
            print(f"  ❌ AI Mapping Error for {factor_symbol}: {e}")
        return None

    # ============================================================
    # STAGE 3: UNIPROT FETCH
    # ============================================================
    def fetch_full_biological_data(self, factor_symbol: str, accession: str) -> Optional[Dict]:
        """Fetches sequence and PTM sites using UniProt."""
        url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
        try:
            print(f"🌐 Stage 3: Fetching Data for {factor_symbol} ({accession})...")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                sequence = data.get("sequence", {}).get("value")
                ptms = [
                    {"description": f.get("description", "Unknown-PTM"), "pos": f.get("location", {}).get("start", {}).get("value")}
                    for f in data.get("features", []) if f.get("type") == "Modified residue"
                ]
                return {"id": factor_symbol, "accession": accession, "sequence": sequence, "ptms": ptms}
        except Exception:
            pass
        return None

    # ============================================================
    # STAGE 4: REFINEMENT
    # ============================================================
    def apply_elite_refinement(self, bio_data: Dict) -> Optional[Dict]:
        """Applies DHL (+15/-15) and maps PTMs."""
        factor = bio_data['id']
        sequence = bio_data['sequence']
        
        # Check registry or use full sequence
        reg = self.isl.get(factor)
        if not reg:
            reg = {"s": 1, "e": len(sequence), "fam": "FullProtein"}
            
        s_elite = max(0, reg['s'] - self.linker_extension - 1)
        e_elite = min(len(sequence), reg['e'] + self.linker_extension)
        elite_seq = sequence[s_elite:e_elite]
        
        mapped_ptms = [
            {"elite_pos": p['pos'] - s_elite, "type": p['description']}
            for p in bio_data['ptms'] if s_elite < p['pos'] <= e_elite
        ]
                
        return {"id": factor, "domain": reg['fam'], "elite_sequence": elite_seq, "elite_len": len(elite_seq), "ptms": mapped_ptms}

    # ============================================================
    # STAGE 5: BUNDLING
    # ============================================================
    def generate_manifest(self, results: List[Dict]) -> List[Dict]:
        """Creates the AF3 discovery manifest."""
        manifest_seqs = [{"dnaSequence": {"sequence": self.z_pillar_dna, "count": 1}}]
        for res in results:
            manifest_seqs.append({"proteinChain": {"sequence": res['elite_sequence'], "count": 1}})
            
        return [{
            "name": f"Zenith_Discovery_Output",
            "sequences": manifest_seqs,
            "model_version": "AlphaFold 3",
            "zenith_ptm_audit": {res['id']: res['ptms'] for res in results}
        }]

def main():
    default_prompt = "Zenith v26.1: Structural Rejuvenation"
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    
    print(f"\n{'='*60}")
    print("🚀 ZENITH v26.1 - INTUITIVE HYBRID DISCOVERY")
    print(f"{'='*60}\n")
    
    engine = ZenithDiscoveryEngine()
    symbols = engine.parse_factors_from_prompt(user_prompt)
    print(f"  🔎 Discovered candidates: {', '.join(symbols)}")
    
    refined_batch = []
    for sym in symbols:
        acc = engine.map_to_uniprot_accession(sym)
        if acc:
            bio = engine.fetch_full_biological_data(sym, acc)
            if bio:
                refined = engine.apply_elite_refinement(bio)
                if refined:
                    print(f"  ✅ {refined['id']:8} | ID: {acc:6} | PTMs: {len(refined['ptms'])}")
                    refined_batch.append(refined)

    if refined_batch:
        manifest = engine.generate_manifest(refined_batch)
        with open("ZENITH_FINAL_VALIDATION_MANIFEST.json", "w") as f:
            json.dump(manifest, f, indent=4)
        print(f"\n✨ COMPLETE: ZENITH_FINAL_VALIDATION_MANIFEST.json created.")
    else:
        print("\n❌ Error: No factors were successfully processed.")

if __name__ == "__main__":
    main()
