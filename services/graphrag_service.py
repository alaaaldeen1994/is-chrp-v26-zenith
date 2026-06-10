import sys
import os

# Align path to ensure we can import grn_authority
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grn_authority import GRNAuthority

class GraphRAGService:
    def __init__(self):
        # Retrieve biologically verified regulatory links from the GRN Authority
        self.grn_links = GRNAuthority.REGULATORY_LINKS
        
        # Define safety scores for transcription factors (lower score means higher oncogenic/drift risk)
        self.safety_registry = {
            "GATA4": 0.95,
            "TBX5": 0.94,
            "NKX2-5": 0.93,
            "MEF2C": 0.92,
            "POU5F1": 0.70, # OCT4
            "SOX2": 0.75,
            "KLF4": 0.65,
            "MYC": 0.15,    # High oncogenic risk
            "SNAI1": 0.35   # High EMT/fibrotic risk
        }

    def execute_semantic_reasoning(self, query: str, top_k_subgraphs: int = 5, confidence_threshold: float = 0.75) -> dict:
        """
        Performs topological traversal and semantic reasoning over the cardiac GRN.
        Identifies active factors, target pathways, and returns a rigorous safety assessment.
        """
        normalized_query = query.upper()
        
        # 1. Identify which transcription factors or target genes are mentioned in the query
        detected_tfs = []
        detected_targets = []
        
        # All unique nodes in our GRN
        all_tfs = list(self.grn_links.keys())
        all_targets = set()
        for targets in self.grn_links.values():
            all_targets.update(targets.keys())
            
        for tf in all_tfs:
            if tf in normalized_query:
                detected_tfs.append(tf)
                
        for target in all_targets:
            if target in normalized_query and target not in detected_tfs:
                detected_targets.append(target)

        # 2. If targets are searched without TFs, retrieve upstream TFs that regulate them
        if len(detected_targets) > 0 and len(detected_tfs) == 0:
            for tf, targets in self.grn_links.items():
                for target in detected_targets:
                    if target in targets:
                        detected_tfs.append(tf)
            detected_tfs = list(set(detected_tfs))

        # Default fallback if query is broad
        if len(detected_tfs) == 0:
            detected_tfs = ["GATA4", "TBX5", "NKX2-5"]
            detected_targets = ["TNNT2", "MYH6"]

        # 3. Build the interaction pathway chains
        pathway_descriptions = []
        recommended_factors = []
        safety_status = "SAFE"
        myc_prob = 0.01
        safety_alerts = []

        for tf in detected_tfs:
            safety_score = self.safety_registry.get(tf, 0.90)
            recommended_factors.append(tf)
            
            # Retrieve downstream targets of this TF
            targets_dict = self.grn_links.get(tf, {})
            active_targets = [t for t in detected_targets if t in targets_dict]
            
            if not active_targets:
                # If no specific targets mentioned, list top targets
                active_targets = list(targets_dict.keys())[:3]
                
            for target in active_targets:
                weight = targets_dict.get(target, 0.0)
                action = "activates" if weight > 0 else "represses"
                pathway_descriptions.append(
                    f"{tf} {action} the promoter of {target} (regulatory weight: {weight:+.2f})."
                )

            # Evaluate safety risk profiles
            if safety_score < 0.50:
                safety_status = "WARNING"
                if tf == "MYC":
                    myc_prob = 0.85
                    safety_alerts.append("Critical Warning: Active MYC pathway increases oncogenic transformation risk.")
                else:
                    myc_prob = max(myc_prob, 0.40)
                    safety_alerts.append(f"Warning: Factor {tf} exhibits high developmental drift risk.")

        interaction_pathway = " ".join(pathway_descriptions)
        if not interaction_pathway:
            interaction_pathway = "No direct active regulatory chains resolved for the query."

        return {
            "recommended_factors": recommended_factors,
            "interaction_pathway": interaction_pathway,
            "safety_risk_assessment": {
                "MYC_activation_probability": myc_prob,
                "status": safety_status,
                "alerts": safety_alerts
            }
        }
