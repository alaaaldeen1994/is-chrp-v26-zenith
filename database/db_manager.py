"""
Zenith Database Manager — Persistence & Audit Trail
===================================================
Provides asynchronous SQLite persistence for all Zenith Phase 1-5 engine runs.
"""

import json
import sqlite3
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "zenith_master.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_db():
    """Ensure database file and tables exist."""
    conn = sqlite3.connect(DB_PATH)
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.close()


def save_prs_result(patient_id: str, phenotype: str, result: Dict[str, Any]):
    """Persist Polygenic Risk Score result."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    top_gene = result.get("crispr_correction_priority", [{}])[0].get("gene", "GATA4")
    conn.execute(
        """
        INSERT INTO polygenic_risk_scores 
        (patient_id, phenotype, additive_prs_score, epistatic_prs_score, population_percentile, horvath_age_acceleration_years, top_driver_gene)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            phenotype,
            result.get("additive_prs", 0.0),
            result.get("epistatic_prs", 0.0),
            result.get("percentile", 50.0),
            result.get("horvath_age_acceleration_years", 0.0),
            top_gene,
        ),
    )
    conn.commit()
    conn.close()


def save_dossier(dossier_id: str, patient_id: str, target_disease: str, result: Dict[str, Any]):
    """Persist Scientific Agent Dossier."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    driver_gene = result.get("final_clinical_recommendation", {}).get("causal_driver_gene", "GATA4")
    exec_time = result.get("dossier_metadata", {}).get("total_execution_time_seconds", 0.0)
    conn.execute(
        """
        INSERT OR REPLACE INTO scientific_dossiers 
        (dossier_id, patient_id, target_disease, total_execution_time_seconds, causal_driver_gene, dossier_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            dossier_id,
            patient_id,
            target_disease,
            exec_time,
            driver_gene,
            json.dumps(result),
        ),
    )
    conn.commit()
    conn.close()


# Ensure DB is initialized on module load
init_db()
