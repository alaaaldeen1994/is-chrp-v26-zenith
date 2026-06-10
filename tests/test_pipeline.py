import sys
import os
import json

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.pipeline_orchestrator import PipelineOrchestrator

def test_pipeline_qc_pass():
    service = PipelineOrchestrator()
    metrics = {
        "total_reads": 100000,
        "mapped_reads": 85000,
        "mitochondrial_reads": 8000,
        "cell_count": 1000
    }
    
    result = service.parse_nextflow_telemetry(json.dumps(metrics))
    
    assert "alignment_rate" in result
    assert result["alignment_rate"] == 0.85
    assert result["mitochondrial_leakage_percent"] == 8.0
    assert result["pipeline_quality_status"] == "PASS"
    assert result["recommended_action"] == "PROCEED"

def test_pipeline_qc_fail_alignment():
    service = PipelineOrchestrator()
    # Alignment rate is 50% (< 80% threshold)
    metrics = {
        "total_reads": 100000,
        "mapped_reads": 50000,
        "mitochondrial_reads": 5000,
        "cell_count": 1000
    }
    
    result = service.parse_nextflow_telemetry(json.dumps(metrics))
    
    assert result["pipeline_quality_status"] == "FAIL"
    assert result["recommended_action"] == "RE-SEQUENCE"
    assert "alignment" in result["qc_audit_summary"].lower()

def test_pipeline_qc_fail_mitochondrial():
    service = PipelineOrchestrator()
    # Mitochondrial read fraction is 20% (> 15% threshold)
    metrics = {
        "total_reads": 100000,
        "mapped_reads": 90000,
        "mitochondrial_reads": 20000,
        "cell_count": 1000
    }
    
    result = service.parse_nextflow_telemetry(json.dumps(metrics))
    
    assert result["pipeline_quality_status"] == "FAIL"
    assert result["recommended_action"] == "RE-SEQUENCE"
    assert "mitochondrial" in result["qc_audit_summary"].lower()

if __name__ == "__main__":
    print("Running Pipeline Orchestrator unit tests...")
    test_pipeline_qc_pass()
    test_pipeline_qc_fail_alignment()
    test_pipeline_qc_fail_mitochondrial()
    print("All tests passed!")
