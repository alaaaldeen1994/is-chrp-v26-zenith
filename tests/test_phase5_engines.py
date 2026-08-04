"""
Phase 5 Zenith Intelligence Layer Test Suite
=============================================
Validates:
  1. Zenith Scientific AI Agent Pipeline (10 steps)
  2. Zenith Biological Knowledge Graph Query Engine
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.zenith_ai_agent import run_zenith_scientific_agent_pipeline
from database.knowledge_graph import query_knowledge_graph


class TestPhase5Services(unittest.TestCase):

    def test_zenith_ai_agent_pipeline(self):
        res = run_zenith_scientific_agent_pipeline(patient_id="TEST_PATIENT_001", target_organ="heart")

        self.assertEqual(res["dossier_metadata"]["pipeline_status"], "SUCCESS")
        self.assertIn("final_clinical_recommendation", res)
        self.assertEqual(len(res["execution_log"]), 10)
        self.assertGreater(res["dossier_metadata"]["total_execution_time_seconds"], 0.0)
        print("Zenith Scientific AI Agent Pipeline Test: PASSED")

    def test_knowledge_graph_query(self):
        res = query_knowledge_graph(source_node="GATA4", max_hops=2)

        self.assertGreater(res["paths_found_count"], 0)
        self.assertIn("MYH7", res["connected_nodes"])
        print("Zenith Knowledge Graph Query Test: PASSED")


if __name__ == "__main__":
    unittest.main()
