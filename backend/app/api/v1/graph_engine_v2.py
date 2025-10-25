from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.services.graph_engine_v2 import graph_engine_v2, PathConstraint, CostFunction

router = APIRouter()


class PathConstraintModel(BaseModel):
    max_hops: int = Field(10, ge=1, le=20)
    min_amount: float = Field(0.0, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    risk_threshold: float = Field(1.0, ge=0.0, le=1.0)
    time_window_days: int = Field(365, ge=1, le=3650)
    chains: Optional[list[str]] = None
    exclude_addresses: Optional[list[str]] = None
    include_tags: Optional[list[str]] = None
    exclude_tags: Optional[list[str]] = None


class CostFunctionModel(BaseModel):
    transaction_fee_weight: float = Field(1.0, ge=0)
    time_cost_weight: float = Field(0.1, ge=0)
    risk_penalty_weight: float = Field(10.0, ge=0)
    hop_penalty_weight: float = Field(0.5, ge=0)


class FindPathsRequest(BaseModel):
    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    constraints: PathConstraintModel = Field(default_factory=PathConstraintModel)
    cost_function: CostFunctionModel = Field(default_factory=CostFunctionModel)
    algorithm: str = Field("astar", regex="^(astar|bidirectional)$")
    max_paths: int = Field(10, ge=1, le=50)


class GraphQueryRequest(BaseModel):
    query: Dict[str, Any] = Field(..., description="GraphQL-style query")


@router.get("/subgraph", tags=["Graph Engine v2"])
async def get_subgraph_v2(
    address: str = Query(..., description="Address to explore"),
    max_hops: int = Query(3, ge=1, le=10),
    risk_threshold: float = Query(1.0, ge=0.0, le=1.0),
    min_amount: float = Query(0.0, ge=0.0),
    time_window_days: int = Query(365, ge=1, le=3650),
    include_bridges: bool = Query(True),
    max_nodes: int = Query(500, ge=10, le=2000),
    max_edges: int = Query(1000, ge=10, le=5000),
):
    """Returns a subgraph around an address using Graph Engine v2 constraints."""
    try:
        result = await graph_engine_v2.fetch_subgraph(
            address=address,
            max_hops=max_hops,
            risk_threshold=risk_threshold,
            min_amount=min_amount,
            time_window_days=time_window_days,
            include_bridges=include_bridges,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subgraph fetch failed: {str(e)}")


@router.post("/find-paths", tags=["Graph Engine v2"])
async def find_paths(req: FindPathsRequest):
    """Finde Pfade zwischen zwei Adressen mit Constraints und Cost-Functions"""
    try:
        constraints = PathConstraint(**req.constraints.dict())
        cost_fn = CostFunction(**req.cost_function.dict())

        if req.algorithm == "bidirectional":
            result = await graph_engine_v2.find_paths_bidirectional(
                req.source, req.target, constraints, cost_fn, req.max_paths
            )
        else:
            result = await graph_engine_v2.find_paths_astar(
                req.source, req.target, constraints, cost_fn, req.max_paths
            )

        return {
            "source": result.source,
            "target": result.target,
            "paths": result.paths,
            "execution_time_ms": result.execution_time_ms,
            "total_paths_found": result.total_paths_found,
            "algorithm": req.algorithm
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Path finding failed: {str(e)}")


@router.post("/query", tags=["Graph Engine v2"])
async def query_graph_v2(req: GraphQueryRequest):
    """GraphQL-ähnliche Query API v2"""
    try:
        result = await graph_engine_v2.query_graph_v2(req.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")


@router.post("/materialize-hot-paths", tags=["Graph Engine v2"])
async def materialize_hot_paths(min_frequency: int = Query(100, ge=10, le=1000)):
    """Materialisiere häufig abgefragte Pfade für bessere Performance"""
    try:
        await graph_engine_v2.materialize_hot_paths(min_frequency)
        return {"status": "Hot paths materialized", "min_frequency": min_frequency}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Materialization failed: {str(e)}")


@router.get("/stats", tags=["Graph Engine v2"])
async def get_graph_stats():
    """Statistiken über den Graph Engine"""
    try:
        # Vereinfachte Stats (in Produktion: echte Metriken)
        stats = {
            "enabled": graph_engine_v2.enabled,
            "hot_paths_cached": len(graph_engine_v2._hot_paths_cache),
            "materialized_paths": len(graph_engine_v2._materialized_paths),
            "supported_algorithms": ["astar", "bidirectional"],
            "max_hops_supported": 20,
            "performance_target_ms": 1500
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")
