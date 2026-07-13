"""SQLAlchemy models for NEUROS-X neural analysis caching.

Add these to your existing database/models.py (or import this file).

Follows the same pattern as your StructureCache table:
  - SHA-256 hash as the unique key
  - JSON result stored as Text
  - created_at timestamp
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Use the SAME Base as your existing models.py so tables share a registry.
# If your models.py already has `Base = declarative_base()`, import that instead.
try:
    # Attempt to import your existing Base (adjust the import path)
    from database.models import Base as ExistingBase
    Base = ExistingBase
except ImportError:
    Base = declarative_base()


class NeuralAnalysisCache(Base):
    """Cache for neural substrate analyses (ion-profile -> phi/synchrony/ecg).

    Keyed by SHA-256 of the expression vector — same pattern as StructureCache.
    """
    __tablename__ = "neural_analysis_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_hash = Column(String(64), unique=True, index=True, nullable=False)
    expression_summary = Column(String(500), nullable=True)  # human-readable
    result_json = Column(Text, nullable=False)               # full result dict
    n_genes = Column(Integer, nullable=True)
    n_markers_detected = Column(Integer, nullable=True)
    phi_hat = Column(String(32), nullable=True)              # store as string for precision
    neural_age = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<NeuralAnalysisCache hash={self.signal_hash[:8]}... age={self.neural_age}>"


class DualAgeRecord(Base):
    """Persists dual-age (Horvath + Neural) assessments for audit trails.

    Part of the Evidence Registry — every dual-age assessment is logged
    for regulatory compliance and reproducibility.
    """
    __tablename__ = "dual_age_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_hash = Column(String(64), unique=True, index=True, nullable=False)
    chronological_age = Column(String(16), nullable=False)
    horvath_age = Column(String(16), nullable=False)
    neural_age = Column(String(16), nullable=False)
    phenotype = Column(String(32), nullable=False)
    phi_hat = Column(String(32), nullable=True)
    confidence = Column(String(16), nullable=True)
    full_result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<DualAgeRecord horvath={self.horvath_age} neural={self.neural_age} phenotype={self.phenotype}>"


# ---------------------------------------------------------------------------
# Cache helpers (same async pattern as your boltz cache)
# ---------------------------------------------------------------------------

async def get_cached_neural_analysis(session, signal_hash: str) -> Optional[Dict[str, Any]]:
    """Look up a cached neural analysis by its SHA-256 hash."""
    import json
    try:
        row = session.query(NeuralAnalysisCache).filter_by(
            signal_hash=signal_hash
        ).first()
        if row:
            return json.loads(row.result_json)
    except Exception as e:
        logger.warning(f"cache lookup failed: {e}")
    return None


async def store_neural_analysis(session, signal_hash: str, result: Dict[str, Any],
                                expression_summary: str = "") -> None:
    """Store a neural analysis result in the cache."""
    import json
    try:
        existing = session.query(NeuralAnalysisCache).filter_by(
            signal_hash=signal_hash
        ).first()
        if existing:
            # update
            existing.result_json = json.dumps(result)
            existing.expression_summary = expression_summary
            existing.n_genes = result.get("n_genes")
            existing.n_markers_detected = result.get("n_markers_detected")
            existing.phi_hat = str(result.get("phi_hat", ""))
            existing.neural_age = str(result.get("neural_age", ""))
        else:
            row = NeuralAnalysisCache(
                signal_hash=signal_hash,
                expression_summary=expression_summary,
                result_json=json.dumps(result),
                n_genes=result.get("n_genes"),
                n_markers_detected=result.get("n_markers_detected"),
                phi_hat=str(result.get("phi_hat", "")),
                neural_age=str(result.get("neural_age", "")),
            )
            session.add(row)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.warning(f"cache store failed: {e}")


import logging
logger = logging.getLogger("neural_models")
