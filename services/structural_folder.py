import time
import httpx
import re
import math
from typing import Dict, Any
from config.settings import settings

class StructuralFolderService:
    """
    Service to fold amino acid sequences using Meta's ESMFold deep learning model.
    Queries the public ESMFold API endpoint for 3D PDB coordinates,
    with an automatic synthetic fallback if the network or remote host fails.
    """
    
    def fold_sequence(self, sequence: str) -> Dict[str, Any]:
        """
        Submits sequence to ESMFold, returning coordinates in PDB format.
        """
        # 1. Validation
        if not sequence or not sequence.strip():
            return {"status": "error", "error_type": "validation_empty", "message": "Amino acid sequence cannot be empty."}
            
        cleaned_seq = sequence.strip().upper()
        
        # Check length limit
        if len(cleaned_seq) > settings.ESMFOLD_MAX_SEQUENCE_LENGTH:
            return {
                "status": "error",
                "error_type": "validation_too_long",
                "message": f"Sequence length {len(cleaned_seq)} exceeds maximum allowed limit of {settings.ESMFOLD_MAX_SEQUENCE_LENGTH}."
            }
            
        # Check standard amino acid alphabet: ARNDCQEGHILKMFPSTWYV
        invalid_chars = re.sub(r'[ARNDCQEGHILKMFPSTWYV]', '', cleaned_seq)
        if invalid_chars:
            return {
                "status": "error",
                "error_type": "validation_invalid_chars",
                "message": f"Sequence contains invalid amino acid characters: {', '.join(sorted(list(set(invalid_chars))))}."
            }
            
        # Validate settings.ESMFOLD_ENABLED
        if not settings.ESMFOLD_ENABLED:
            if settings.ESMFOLD_FALLBACK_ENABLED:
                return self._generate_fallback_pdb(cleaned_seq, "ESMFold is disabled in settings")
            else:
                return {
                    "status": "error",
                    "error_type": "disabled",
                    "message": "ESMFold service is disabled and fallback is not enabled."
                }

        start_time = time.time()
        
        try:
            # Query ESMFold endpoint with timeout
            print(f"[ESMFold] Submitting sequence of length {len(cleaned_seq)} to ESMFold API at {settings.ESMFOLD_API_URL}...")
            
            with httpx.Client(timeout=float(settings.ESMFOLD_TIMEOUT_SECONDS)) as client:
                response = client.post(
                    settings.ESMFOLD_API_URL,
                    content=cleaned_seq,
                    headers={"Content-Type": "text/plain"}
                )
                
            if response.status_code == 200:
                pdb_content = response.text
                
                # Verify that returned output contains valid PDB-style records (e.g. ATOM, HETATM, TER, END)
                if not pdb_content or not any(x in pdb_content for x in ["ATOM  ", "HETATM", "HEADER", "TER"]):
                    raise ValueError("External service returned empty or invalid PDB data format.")
                    
                duration = time.time() - start_time
                print(f"[ESMFold] Success! Prediction completed in {duration:.2f}s.")
                
                # Extract average pLDDT from PDB records if possible, otherwise default to typical value
                plddt_val = None
                atom_lines = [line for line in pdb_content.splitlines() if line.startswith("ATOM  ")]
                if atom_lines:
                    # In PDB files, column 61-66 is B-factor (for ESMFold, this stores the residue pLDDT score)
                    try:
                        b_factors = [float(line[60:66].strip()) for line in atom_lines]
                        plddt_val = round(sum(b_factors) / len(b_factors), 2)
                    except Exception:
                        pass
                
                return {
                    "status": "success",
                    "source": "ESMFold-Live",
                    "fallback_used": False,
                    "provider_status": "ok",
                    "pdb_data": pdb_content,
                    "metrics": {
                        "length": len(cleaned_seq),
                        "compute_time_sec": round(duration, 2),
                        "predicted_lddt": plddt_val
                    }
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"[ESMFold] Remote service returned status: {response.status_code}. Using fallback...")
                if settings.ESMFOLD_FALLBACK_ENABLED:
                    return self._generate_fallback_pdb(cleaned_seq, f"ESMFold API Error: {error_msg}")
                else:
                    return {
                        "status": "error",
                        "error_type": "provider_error",
                        "message": f"External ESMFold provider failed with status {response.status_code} and fallback is disabled."
                    }
                
        except Exception as e:
            error_msg = str(e)
            print(f"[ESMFold] Connection error: {error_msg}. Using fallback...")
            if settings.ESMFOLD_FALLBACK_ENABLED:
                return self._generate_fallback_pdb(cleaned_seq, f"Connection Failed: {error_msg}")
            else:
                return {
                    "status": "error",
                    "error_type": "provider_error",
                    "message": f"External ESMFold provider connection failed: {error_msg} and fallback is disabled."
                }

    def _generate_fallback_pdb(self, sequence: str, reason: str) -> Dict[str, Any]:
        """Generates a syntactically correct fallback PDB structure file."""
        lines = [
            f"REMARK 250 ESMFold API call failed: {reason}",
            f"REMARK 250 Generated synthetic biological residue coordinates as fallback.",
            f"TITLE     Synthetic fold projection - Zenith v30.0"
        ]
        
        # Simple helix simulation for fallback visualization
        r = 2.3  # Helix radius
        z_step = 1.5  # helical rise per residue
        ang_step = 1.7  # ~100 degrees helical rotation
        
        atom_index = 1
        for res_idx, aa in enumerate(sequence):
            theta = res_idx * ang_step
            x = r * math.sin(theta)
            y = r * math.cos(theta)
            z = res_idx * z_step
            
            # Map single letter AA code to three-letter residue name
            res_map = {
                'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP', 'C': 'CYS',
                'E': 'GLU', 'Q': 'GLN', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
                'L': 'LEU', 'K': 'LYS', 'M': 'MET', 'F': 'PHE', 'P': 'PRO',
                'S': 'SER', 'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
            }
            res_name = res_map.get(aa, 'ALA')
            
            # Atom line format matching PDB standard
            lines.append(
                f"ATOM  {atom_index:>5}  CA  {res_name} A{res_idx+1:>4}    {x:>8.3f}{y:>8.3f}{z:>8.3f}  1.00 45.20           C"
            )
            atom_index += 1
            
        lines.append("TER")
        lines.append("END")
        
        return {
            "status": "success",
            "source": "Zenith-Synthetic-Fallback",
            "fallback_used": True,
            "provider_status": "external_provider_failed",
            "provider_error": reason,
            "pdb_data": "\n".join(lines),
            "metrics": {
                "length": len(sequence),
                "compute_time_sec": 0.01,
                "predicted_lddt": 50.0
            },
            "warning": "External ESMFold provider failed. Synthetic fallback coordinates were generated and should not be interpreted as real protein folding output."
        }
