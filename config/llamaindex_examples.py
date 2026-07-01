"""
LlamaIndex Integration Example for Nilus Lab Zenith API.
Exposes ZenithClient calls as LlamaIndex FunctionTools.
"""

from typing import List, Dict
from llama_index.core.tools import FunctionTool
from zenith import ZenithClient

# Initialize the client
client = ZenithClient()

def safety_audit_fn(factors: List[str]) -> Dict[str, list]:
    """
    Evaluates candidate reprogramming factors for safety and filters out oncogenic factors like MYC.
    """
    return client.safety_audit(factors=factors)

def lnp_optimization_fn(ionizable: float, helper: float, cholesterol: float, peg: float, np_ratio: float) -> Dict[str, float]:
    """
    Optimizes Lipid Nanoparticle (LNP) packaging ratios to target target organs.
    """
    molar_ratios = {
        "ionizable": ionizable,
        "helper": helper,
        "cholesterol": cholesterol,
        "peg": peg
    }
    return client.optimize_lnp(molar_ratios=molar_ratios, np_ratio=np_ratio)

# Wrap functions as LlamaIndex FunctionTools
safety_tool = FunctionTool.from_defaults(
    fn=safety_audit_fn,
    name="safety_audit",
    description="Evaluates candidate transcription factors for safety and filters oncogenic factors."
)

lnp_tool = FunctionTool.from_defaults(
    fn=lnp_optimization_fn,
    name="optimize_lnp",
    description="Simulates LNP molar ratios to maximize cell tropism selectivity."
)

if __name__ == "__main__":
    print("Exposing Zenith LlamaIndex Tools:")
    print("- Name:", safety_tool.metadata.name)
    print("- Description:", safety_tool.metadata.description)
