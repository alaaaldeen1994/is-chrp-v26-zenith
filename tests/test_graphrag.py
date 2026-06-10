import sys
import os

# Align path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.graphrag_service import GraphRAGService

def test_graphrag_reasoning_gata4():
    service = GraphRAGService()
    # Test query mentioning GATA4
    result = service.execute_semantic_reasoning("What are the target genes for GATA4 in heart cells?")
    
    assert "recommended_factors" in result
    assert "GATA4" in result["recommended_factors"]
    assert "interaction_pathway" in result
    assert "TNNT2" in result["interaction_pathway"] or "MYH6" in result["interaction_pathway"]
    assert result["safety_risk_assessment"]["status"] == "SAFE"
    assert result["safety_risk_assessment"]["MYC_activation_probability"] == 0.01

def test_graphrag_reasoning_myc():
    service = GraphRAGService()
    # Test query mentioning MYC (high-risk oncogenic factor)
    result = service.execute_semantic_reasoning("Evaluate safety of inserting MYC factor in cardiomyocytes.")
    
    assert "MYC" in result["recommended_factors"]
    assert result["safety_risk_assessment"]["status"] == "WARNING"
    assert result["safety_risk_assessment"]["MYC_activation_probability"] == 0.85
    assert len(result["safety_risk_assessment"]["alerts"]) > 0

def test_graphrag_fallback():
    service = GraphRAGService()
    # Test broad query fallback
    result = service.execute_semantic_reasoning("Show me the general rejuvenation factors.")
    
    assert "GATA4" in result["recommended_factors"]
    assert "TBX5" in result["recommended_factors"]
    assert result["safety_risk_assessment"]["status"] == "SAFE"

if __name__ == "__main__":
    print("Running GraphRAG unit tests...")
    test_graphrag_reasoning_gata4()
    test_graphrag_reasoning_myc()
    test_graphrag_fallback()
    print("All tests passed!")
