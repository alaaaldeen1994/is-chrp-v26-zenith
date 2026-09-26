import time
import httpx
import re
import math
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from config.settings import settings
from database.models import StructureCache

class StructuralFolderService:
    """
    Service to fold amino acid sequences using Meta's ESMFold deep learning model.
    Queries the public ESMFold API endpoint for 3D PDB coordinates,
    with an automatic synthetic fallback if the network or remote host fails.
    """
    
    def fold_sequence(self, sequence: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Submits sequence to ESMFold, returning coordinates in PDB format.
        """
        start_time = time.time()
        
        # 1. Input Validation
        if not sequence or not sequence.strip():
            return {
                "status": "error",
                "error_type": "validation_empty",
                "message": "Amino acid sequence cannot be empty."
            }
            
        cleaned_seq = sequence.strip().upper()
        
        # Enforce max sequence length
        if len(cleaned_seq) > settings.ESMFOLD_MAX_SEQUENCE_LENGTH:
            return {
                "status": "error",
                "error_type": "validation_too_long",
                "message": f"Sequence length {len(cleaned_seq)} exceeds maximum allowed limit of {settings.ESMFOLD_MAX_SEQUENCE_LENGTH}."
            }
            
        # Reject nucleotide/DNA sequences if detected
        if len(cleaned_seq) >= 8 and all(c in "ACGTUN" for c in cleaned_seq):
            return {
                "status": "error",
                "error_type": "validation_invalid_chars",
                "message": "Nucleotide (DNA/RNA) sequences are not supported. Please provide a protein amino acid sequence."
            }
            
        # Check standard amino acid alphabet: ARNDCQEGHILKMFPSTWYV (allow X for unknown residue)
        invalid_chars = re.sub(r'[ARNDCQEGHILKMFPSTWYVX]', '', cleaned_seq)
        if invalid_chars:
            return {
                "status": "error",
                "error_type": "validation_invalid_chars",
                "message": f"Sequence contains invalid amino acid characters: {', '.join(sorted(list(set(invalid_chars))))}."
            }
            
        # 2. Caching layer
        sequence_hash = hashlib.sha256(cleaned_seq.encode()).hexdigest()
        
        if settings.ESMFOLD_CACHE_ENABLED and db is not None:
            try:
                cached_entry = db.query(StructureCache).filter(StructureCache.sequence_hash == sequence_hash).first()
                if cached_entry and cached_entry.source != "Zenith-Synthetic-Fallback":
                    duration = time.time() - start_time
                    metrics = {
                        "length": cached_entry.metrics_length,
                        "compute_time_sec": cached_entry.metrics_compute_time_sec,
                        "predicted_lddt": cached_entry.metrics_predicted_lddt,
                        "confidence_source": "pLDDT/B-factor-derived" if cached_entry.metrics_predicted_lddt is not None else "N/A"
                    }
                    return {
                        "status": "success",
                        "source": cached_entry.source,
                        "fallback_used": (cached_entry.source == "Zenith-Synthetic-Fallback"),
                        "provider": settings.ESMFOLD_PROVIDER_NAME,
                        "provider_status": cached_entry.provider_status,
                        "sequence_length": len(cleaned_seq),
                        "pdb_data": cached_entry.pdb_data,
                        "metrics": metrics,
                        "cache_hit": True,
                        "scientific_limitations": self._get_scientific_limitations(cached_entry.source == "Zenith-Synthetic-Fallback"),
                        **({"warning": "External ESMFold provider failed. Synthetic fallback coordinates were generated and should not be interpreted as real protein folding output."} if cached_entry.source == "Zenith-Synthetic-Fallback" else {})
                    }
            except Exception as ce:
                print(f"[ESMFold] Cache read error: {ce}")

        # 3. Check settings.ESMFOLD_ENABLED
        if not settings.ESMFOLD_ENABLED:
            return {
                "status": "error",
                "error_type": "disabled",
                "message": "ESMFold service is disabled in settings."
            }

        # 4. Query live ESMFold provider
        try:
            print(f"[ESMFold] Submitting sequence of length {len(cleaned_seq)} to ESMFold API at {settings.ESMFOLD_API_URL}...")
            
            with httpx.Client(timeout=float(settings.ESMFOLD_TIMEOUT_SECONDS)) as client:
                response = client.post(
                    settings.ESMFOLD_API_URL,
                    content=cleaned_seq,
                    headers={"Content-Type": "text/plain"}
                )
                
            if response.status_code == 200:
                pdb_content = response.text
                
                # Standardise PDB termination if missing from provider
                if pdb_content and not pdb_content.endswith("\n"):
                    pdb_content += "\n"
                if pdb_content and "TER" not in pdb_content:
                    pdb_content += "TER\n"
                if pdb_content and "END" not in pdb_content:
                    pdb_content += "END\n"
                
                # Verify that returned output contains valid PDB-style records
                if not self._validate_pdb_content(pdb_content, len(cleaned_seq)):
                    raise ValueError("External service returned empty or invalid PDB data format.")
                    
                duration = time.time() - start_time
                print(f"[ESMFold] Success! Prediction completed in {duration:.2f}s.")
                
                # Extract average pLDDT from PDB records if possible
                plddt_val = self._extract_plddt(pdb_content)
                
                res = {
                    "status": "success",
                    "source": "ESMFold-Live",
                    "fallback_used": False,
                    "provider": settings.ESMFOLD_PROVIDER_NAME,
                    "provider_status": "ok",
                    "sequence_length": len(cleaned_seq),
                    "pdb_data": pdb_content,
                    "metrics": {
                        "length": len(cleaned_seq),
                        "compute_time_sec": round(duration, 2),
                        "predicted_lddt": plddt_val,
                        "confidence_source": "pLDDT/B-factor-derived" if plddt_val is not None else "N/A"
                    },
                    "cache_hit": False,
                    "scientific_limitations": self._get_scientific_limitations(fallback_used=False)
                }
                
                self._save_to_cache_if_enabled(db, sequence_hash, cleaned_seq, res)
                return res
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"[ESMFold] Remote service returned status: {response.status_code}.")
                return {
                    "status": "error",
                    "error_type": "provider_error",
                    "message": f"External ESMFold provider failed with status {response.status_code}."
                }
                
        except Exception as e:
            error_msg = str(e)
            safe_error = re.sub(r'Bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer ****', error_msg)
            print(f"[ESMFold] Connection error: {safe_error}.")
            return {
                "status": "error",
                "error_type": "provider_error",
                "message": f"External ESMFold provider connection failed: {safe_error}."
            }

    def _validate_pdb_content(self, pdb_content: str, expected_length: int) -> bool:
        if not pdb_content or not pdb_content.strip():
            return False
        
        # Check for HTML tags, JSON structures or known authentication error patterns
        if "<html" in pdb_content.lower() or "<!doctype" in pdb_content.lower():
            return False
        if '{"detail"' in pdb_content or '{"message"' in pdb_content:
            return False
        if "unauthorized" in pdb_content.lower() or "missing authentication token" in pdb_content.lower():
            return False
            
        lines = pdb_content.splitlines()
        atom_lines = [line for line in lines if line.startswith("ATOM  ")]
        if not atom_lines:
            return False
            
        # Verify atom lines coordinate columns (at least 54 chars per line)
        for line in atom_lines:
            if len(line) < 54:
                return False
                
        # Verify sequence length and residue count are consistent
        residues = set()
        for line in atom_lines:
            try:
                res_seq = int(line[22:26].strip())
                residues.add(res_seq)
            except ValueError:
                pass
                
        if not residues or len(residues) != expected_length:
            return False
            
        return True

    def _extract_plddt(self, pdb_content: str) -> Optional[float]:
        atom_lines = [line for line in pdb_content.splitlines() if line.startswith("ATOM  ")]
        if atom_lines:
            try:
                # Column 61-66 is B-factor (for ESMFold, this stores the residue pLDDT score)
                b_factors = [float(line[60:66].strip()) for line in atom_lines]
                avg_b = sum(b_factors) / len(b_factors)
                # Map to standard 0.0-1.0 if it is written as 0-100
                if avg_b > 1.0:
                    return round(avg_b / 100.0, 2)
                return round(avg_b, 2)
            except Exception:
                pass
        return None

    def _generate_fallback_pdb(self, sequence: str, reason: str) -> Dict[str, Any]:
        """Decommissioned. Synthetic fallback PDB generation is disabled."""
        raise RuntimeError("Synthetic fallback PDB generation has been decommissioned.")

    def _get_scientific_limitations(self, fallback_used: bool) -> list:
        if fallback_used:
            return [
                "Fallback output is synthetic",
                "Not real ESMFold",
                "Not suitable for structural interpretation",
                "Not suitable for scientific claims"
            ]
        else:
            return [
                "Single-sequence structure prediction only",
                "Not AlphaFold",
                "Not AlphaFold3",
                "Not ligand-aware",
                "Not validated for clinical use"
            ]

    def _save_to_cache_if_enabled(self, db: Optional[Session], sequence_hash: str, sequence: str, result: Dict[str, Any]):
        if not settings.ESMFOLD_CACHE_ENABLED or db is None:
            return
            
        try:
            # Check if it already exists
            exists = db.query(StructureCache).filter(StructureCache.sequence_hash == sequence_hash).first()
            if not exists:
                metrics = result.get("metrics", {})
                cache_entry = StructureCache(
                    sequence_hash=sequence_hash,
                    sequence=sequence,
                    source=result["source"],
                    pdb_data=result["pdb_data"],
                    provider_status=result["provider_status"],
                    metrics_length=metrics.get("length", len(sequence)),
                    metrics_compute_time_sec=metrics.get("compute_time_sec", 0.0),
                    metrics_predicted_lddt=metrics.get("predicted_lddt", None)
                )
                db.add(cache_entry)
                db.commit()
                print(f"[ESMFold] Sequence prediction saved to database cache.")
        except Exception as ce:
            print(f"[ESMFold] Cache write error: {ce}")
            if db:
                db.rollback()
