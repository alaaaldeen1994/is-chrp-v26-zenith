"""
LangChain Integration Example for Nilus Lab Zenith API.
Exposes ZenithClient calls as LangChain tools.
"""

from typing import List, Dict, Optional
from langchain_core.tools import tool
from zenith import ZenithClient

# Initialize the client (reads ZENITH_API_KEY from environment)
client = ZenithClient()

@tool
def safety_audit_tool(factors: List[str]) -> str:
    """
    Evaluates candidate reprogramming factors for safety and filters out oncogenic transcription factors like MYC.
    """
    try:
        result = client.safety_audit(factors=factors)
        return f"Approved factors: {result.get('approved_factors')}. Blocked factors: {result.get('blocked_factors')}."
    except Exception as e:
        return f"Error executing safety audit: {e}"

@tool
def lnp_optimization_tool(ionizable: float, helper: float, cholesterol: float, peg: float, np_ratio: float) -> str:
    """
    Optimizes Lipid Nanoparticle (LNP) packaging ratios to target cardiac tissues.
    """
    try:
        molar_ratios = {
            "ionizable": ionizable,
            "helper": helper,
            "cholesterol": cholesterol,
            "peg": peg
        }
        result = client.optimize_lnp(molar_ratios=molar_ratios, np_ratio=np_ratio)
        return (f"Encapsulation Efficiency: {result.get('encapsulation_efficiency_percent')}%. "
                f"Heart Tropism Score: {result.get('heart_selectivity_score')}.")
    except Exception as e:
        return f"Error optimizing LNP formulation: {e}"

# Example agent definition
if __name__ == "__main__":
    print("Exposing Zenith LangChain Tools:")
    print("- Name:", safety_audit_tool.name)
    print("- Description:", safety_audit_tool.description)
