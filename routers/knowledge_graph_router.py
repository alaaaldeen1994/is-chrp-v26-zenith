"""
Zenith Knowledge Graph Router — Zenith Phase 5
POST /api/v2/knowledge-graph/query
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from database.knowledge_graph import query_knowledge_graph, GRAPH_NODES

router = APIRouter(prefix="/api/v2/knowledge-graph", tags=["Zenith Biological Knowledge Graph"])


class GraphQueryRequest(BaseModel):
    source_node: Optional[str] = Field(
        default="GATA4",
        description="Starting node symbol (e.g. 'GATA4', 'rs2234962', 'TP53', 'Rapamycin')",
    )
    relation_type: Optional[str] = Field(
        default=None,
        description="Optional relation filter: 'activates', 'inhibits', 'associated_with', 'participates_in', 'drives'",
    )
    max_hops: int = Field(
        default=2,
        ge=1,
        le=4,
        description="Maximum graph traversal depth",
    )


class GraphQueryResponse(BaseModel):
    query: Dict[str, Any]
    paths_found_count: int
    connected_nodes: List[str]
    traversed_paths: List[List[Dict[str, Any]]]
    summary: str


@router.post(
    "/query",
    response_model=GraphQueryResponse,
    summary="Query Biological Knowledge Graph (Multi-Hop Traversal)",
    description="""
Multi-hop graph traversal engine across Genes, Proteins, Variants, Drugs, Pathways, and Diseases.
    """,
)
async def query_graph(request: GraphQueryRequest) -> GraphQueryResponse:
    try:
        result = query_knowledge_graph(
            source_node=request.source_node,
            relation_type=request.relation_type,
            max_hops=request.max_hops,
        )
        return GraphQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Knowledge Graph query error: {str(e)}")


@router.get(
    "/schema",
    summary="List Knowledge Graph node types & categories",
)
async def graph_schema() -> Dict[str, Any]:
    return {
        "node_types": GRAPH_NODES,
        "total_nodes": sum(len(v) for v in GRAPH_NODES.values()),
        "supported_relations": ["associated_with", "activates", "inhibits", "participates_in", "drives", "corrects"],
    }


@router.get(
    "/query/demo",
    summary="Demo: Traversal from GATA4 master TF to downstream diseases",
)
async def graph_demo() -> Dict[str, Any]:
    result = query_knowledge_graph(source_node="GATA4", max_hops=2)
    result["demo"] = True
    return result
