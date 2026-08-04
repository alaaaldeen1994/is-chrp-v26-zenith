"""
Zenith Biological Knowledge Graph — Zenith Phase 5
===================================================
A structured, graph-based biological knowledge engine connecting:
  Nodes: Gene | Protein | Variant | Drug | Pathway | Disease | TF
  Edges: regulates | inhibits | activates | causes | treats | targets

Supports multi-hop reasoning queries (e.g. "Find all drugs targeting genes
downstream of GATA4 with GWAS evidence for heart failure").

References:
  - Wishart et al. (2018). DrugBank 5.0. Nucleic Acids Res 46(D1):D1074-D1082.
  - Landrum et al. (2018). ClinVar: improving access to variant interpretations.
    Nucleic Acids Res 46(D1):D1062-D1067.
"""

from typing import Dict, List, Optional, Tuple, Set

# ---------------------------------------------------------------------------
# KNOWLEDGE GRAPH NODES AND EDGES DATABASE
# ---------------------------------------------------------------------------
GRAPH_NODES = {
    "Gene": ["MYH7", "TNNT2", "MYH6", "LMNA", "SCN5A", "NKX2-5", "GATA4", "TBX5", "TP53", "CDKN2A", "TERT", "TERC", "TGFB1", "COL1A1"],
    "Protein": ["GATA4_protein", "NKX2-5_protein", "p53_protein", "p16_INK4a", "Telomerase", "Myosin_7"],
    "Variant": ["rs2234962", "rs7977462", "rs3729547", "rs2042995", "rs11107116", "rs1042522", "rs2811712", "rs10936599"],
    "Drug": ["Aspirin", "Valproic_Acid", "Vitamin_C", "CHIR99021", "Rapamycin", "Metformin", "ABE8e_Editor", "PE3_Editor"],
    "Pathway": ["Cardiac_Contractility", "p53_p16_Senescence", "Pluripotency_Network", "TGFB_Fibrosis", "Telomere_Maintenance"],
    "Disease": ["Hypertrophic_Cardiomyopathy", "Dilated_Cardiomyopathy", "Brugada_Syndrome", "Accelerated_Aging", "Cardiac_Fibrosis"],
}

GRAPH_EDGES = [
    # Variant -> Gene (causes / associated with)
    {"source": "rs2234962", "target": "MYH7", "relation": "associated_with", "evidence": "GWAS UK Biobank"},
    {"source": "rs7977462", "target": "TNNT2", "relation": "associated_with", "evidence": "ClinVar pathogenic"},
    {"source": "rs11107116", "target": "GATA4", "relation": "associated_with", "evidence": "GWAS CHD"},
    {"source": "rs1042522", "target": "TP53", "relation": "associated_with", "evidence": "GWAS Aging"},
    {"source": "rs10936599", "target": "TERC", "relation": "associated_with", "evidence": "GWAS Telomere"},

    # TF / Gene -> Target Gene (regulates / activates / inhibits)
    {"source": "GATA4", "target": "MYH7", "relation": "activates", "evidence": "ChIP-seq + Zenith GRN"},
    {"source": "GATA4", "target": "NKX2-5", "relation": "activates", "evidence": "Master TF co-regulation"},
    {"source": "NKX2-5", "target": "TBX5", "relation": "activates", "evidence": "Synergistic complex"},
    {"source": "TP53", "target": "CDKN2A", "relation": "activates", "evidence": "p53-p16 senescence axis"},
    {"source": "TP53", "target": "TERT", "relation": "inhibits", "evidence": "Transcriptional repression"},

    # Gene -> Pathway (participates_in)
    {"source": "MYH7", "target": "Cardiac_Contractility", "relation": "participates_in", "evidence": "GO:0055001"},
    {"source": "CDKN2A", "target": "p53_p16_Senescence", "relation": "participates_in", "evidence": "GO:0090398"},
    {"source": "TERT", "target": "Telomere_Maintenance", "relation": "participates_in", "evidence": "GO:0000781"},
    {"source": "TGFB1", "target": "TGFB_Fibrosis", "relation": "participates_in", "evidence": "GO:0030198"},

    # Pathway -> Disease (drives / protects)
    {"source": "Cardiac_Contractility", "target": "Hypertrophic_Cardiomyopathy", "relation": "drives_when_dysregulated", "evidence": "Clinical cardiology"},
    {"source": "p53_p16_Senescence", "target": "Accelerated_Aging", "relation": "drives", "evidence": "Hallmarks of Aging"},
    {"source": "TGFB_Fibrosis", "target": "Cardiac_Fibrosis", "relation": "drives", "evidence": "Fibrosis literature"},

    # Drug -> Gene / Pathway (targets / inhibits / treats)
    {"source": "PE3_Editor", "target": "rs2234962", "relation": "corrects", "evidence": "Prime editing design"},
    {"source": "ABE8e_Editor", "target": "rs11107116", "relation": "corrects", "evidence": "Base editing design"},
    {"source": "Rapamycin", "target": "p53_p16_Senescence", "relation": "inhibits", "evidence": "mTOR inhibition anti-aging"},
    {"source": "Valproic_Acid", "target": "Pluripotency_Network", "relation": "activates", "evidence": "HDAC inhibitor reprogramming"},
]


# ---------------------------------------------------------------------------
# Multi-Hop Graph Query Engine
# ---------------------------------------------------------------------------

def query_knowledge_graph(
    source_node: Optional[str] = "GATA4",
    relation_type: Optional[str] = None,
    max_hops: int = 2,
) -> Dict:
    """
    Perform multi-hop traversal query on Zenith Biological Knowledge Graph.

    Args:
        source_node: Starting node (e.g. 'GATA4', 'rs2234962', 'TP53')
        relation_type: Filter by edge relation ('activates', 'inhibits', 'targets', etc.)
        max_hops: Maximum graph traversal depth (default 2)

    Returns:
        Graph query result dict with traversed paths and matched nodes
    """
    paths: List[List[Dict]] = []

    def _traverse(current: str, current_path: List[Dict], depth: int):
        if depth > max_hops:
            return

        for edge in GRAPH_EDGES:
            if edge["source"].lower() == current.lower():
                if relation_type and edge["relation"].lower() != relation_type.lower():
                    continue

                new_path = current_path + [edge]
                paths.append(new_path)
                _traverse(edge["target"], new_path, depth + 1)

    if source_node:
        _traverse(source_node, [], 1)

    # Collect connected nodes
    connected_nodes = set()
    for p in paths:
        for step in p:
            connected_nodes.add(step["source"])
            connected_nodes.add(step["target"])

    return {
        "query": {
            "source_node": source_node,
            "relation_filter": relation_type,
            "max_hops": max_hops,
        },
        "paths_found_count": len(paths),
        "connected_nodes": list(connected_nodes),
        "traversed_paths": paths,
        "summary": (
            f"Knowledge Graph query starting at '{source_node}' yielded {len(paths)} path(s) "
            f"across {len(connected_nodes)} connected node(s) up to {max_hops} hop(s)."
        ),
    }
