import os
import json
import uuid
from structural_authority import StructuralAuthority

class AF3AutomationBridge:
    """
    Zenith AF3 Automation Bridge
    Connects Neural SDE predictions to AlphaFold 3 structural validation.
    """
    
    OUTPUT_DIR = "af3_jobs"
    
    def __init__(self, sequences_path="factor_sequences.json"):
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)
            
        with open(sequences_path, "r") as f:
            self.sequence_registry = json.load(f)

    def generate_structural_job(self, primary_tf, secondary_tf=None, dna_sequence="CCTGTGACTGTGGGGTTCACGCTCCCGGGTG"):
        """
        Generates a validated AlphaFold 3 Multimer JSON manifest for the predicted interaction.
        """
        print(f"\n[AF3 BRIDGE] Generating Structural Validation for: {primary_tf}" + (f" + {secondary_tf}" if secondary_tf else ""))
        
        entities = []
        
        # Process Primary TF
        primary_meta = StructuralAuthority.get_factor_metadata(primary_tf)
        if not primary_meta:
            return {"status": "error", "message": f"Primary TF {primary_tf} not in structural registry"}
            
        std_symbol = primary_meta["symbol"]
        primary_seq = self.sequence_registry.get(std_symbol.upper())
        if not primary_seq:
            return {"status": "error", "message": f"Sequence for {std_symbol} missing from registry"}
            
        # Extract verified domain
        domain_range = primary_meta["residues"].split("-")
        start, end = int(domain_range[0]), int(domain_range[1])
        # We add 20bp padding for stability
        safe_start = max(1, start - 20)
        safe_end = min(len(primary_seq), end + 20)
        
        primary_domain_seq = primary_seq[safe_start-1:safe_end]
        entities.append({
            "proteinChain": {
                "sequence": primary_domain_seq,
                "count": 1
            }
        })
        print(f"  > Primary TF: {primary_tf} ({primary_meta['domain_name']} Domain, {len(primary_domain_seq)}aa)")

        # Process Secondary TF (if dimerization is predicted)
        if secondary_tf:
            secondary_meta = StructuralAuthority.get_factor_metadata(secondary_tf)
            if secondary_meta:
                s_std_symbol = secondary_meta["symbol"]
                secondary_seq = self.sequence_registry.get(s_std_symbol.upper())
                if secondary_seq:
                    s_range = secondary_meta["residues"].split("-")
                    s_start, s_end = int(s_range[0]), int(s_range[1])
                    s_safe_start = max(1, s_start - 20)
                    s_safe_end = min(len(secondary_seq), s_end + 20)
                    
                    secondary_domain_seq = secondary_seq[s_safe_start-1:s_safe_end]
                    entities.append({
                        "proteinChain": {
                            "sequence": secondary_domain_seq,
                            "count": 1
                        }
                    })
                    print(f"  > Secondary TF: {secondary_tf} ({secondary_meta['domain_name']} Domain, {len(secondary_domain_seq)}aa)")

        # Add DNA interaction target
        if dna_sequence:
            entities.append({
                "dnaSequence": {
                    "sequence": dna_sequence,
                    "count": 1
                }
            })
            print(f"  > DNA Target: {dna_sequence[:10]}... ({len(dna_sequence)}bp)")

        # Build Final Manifest
        job_id = f"Zenith_AF3_{primary_tf}" + (f"_{secondary_tf}" if secondary_tf else "") + f"_{str(uuid.uuid4())[:8]}"
        manifest = {
            "name": job_id,
            "modelSeeds": [42],
            "sequences": entities,
            "dialect": "alphafold3",
            "version": 1
        }
        
        filepath = os.path.join(self.OUTPUT_DIR, f"{job_id}.json")
        with open(filepath, "w") as f:
            json.dump(manifest, f, indent=2)
            
        print(f"[AF3 BRIDGE] Manifest generated: {filepath}\n")
        return {"status": "success", "job_id": job_id, "filepath": filepath, "manifest": manifest}

if __name__ == "__main__":
    # Demo automation run
    bridge = AF3AutomationBridge()
    
    # Scenario: Zenith predicts a POU5F1-SOX2 heterodimer for pluripotency induction
    bridge.generate_structural_job("POU5F1", "SOX2")
    
    # Scenario: Zenith predicts GATA4 activation in cardiac rejuvenation
    bridge.generate_structural_job("GATA4")
