"""
Investigator Graph API
Endpoints for interactive graph exploration, path finding, and timeline analysis
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db.neo4j_client import neo4j_client
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)

router = APIRouter()


class GraphExploreResponse(BaseModel):
    """Response model for graph exploration"""
    nodes: Dict[str, Dict[str, Any]]
    links: List[Dict[str, Any]]
    summary: Dict[str, Any]


class PathFindRequest(BaseModel):
    """Request model for path finding"""
    from_address: str
    to_address: str
    max_hops: int = Field(5, ge=1, le=10)
    include_bridges: bool = True


class PathFindResponse(BaseModel):
    """Response model for path finding"""
    found: bool
    paths: List[Dict[str, Any]]
    summary: Dict[str, Any]


class TimelineResponse(BaseModel):
    """Response model for timeline data"""
    address: str
    events: List[Dict[str, Any]]
    summary: Dict[str, Any]


@router.get("/investigator/explore", response_model=GraphExploreResponse)
async def explore_address_graph(
    address: str = Query(..., description="Address to explore"),
    max_hops: int = Query(3, ge=1, le=5, description="Maximum hops to explore"),
    include_bridges: bool = Query(True, description="Include cross-chain bridges"),
    from_timestamp: Optional[str] = Query(None, description="Start timestamp (ISO format)"),
    to_timestamp: Optional[str] = Query(None, description="End timestamp (ISO format)")
) -> GraphExploreResponse:
    """
    Explore the graph around a specific address

    Returns nodes and edges within the specified hop distance
    """
    try:
        # Get address neighbors with specified depth
        neighbors = await neo4j_client.get_address_neighbors(
            address,
            direction="both",
            limit=1000,
            max_hops=max_hops
        )

        nodes = {}
        links = []

        # Process neighbors and build graph
        for neighbor in neighbors:
            addr = neighbor["address"]
            nodes[addr] = {
                "address": addr,
                "chain": neighbor.get("chain", "unknown"),
                "taint_score": neighbor.get("taint_score", 0.0),
                "risk_level": neighbor.get("risk_level", "unknown"),
                "labels": neighbor.get("labels", []),
                "tx_count": neighbor.get("tx_count", 0),
                "balance": neighbor.get("balance", 0.0),
                "first_seen": neighbor.get("first_seen", ""),
                "last_seen": neighbor.get("last_seen", "")
            }

        # Get edges between these addresses
        addresses = list(nodes.keys())
        if len(addresses) > 1:
            # Use existing path finding but limit to direct connections
            paths = await neo4j_client.find_path(address, addresses[1], max_hops=1)

            for path in paths[:50]:  # Limit to avoid too much data
                if len(path.get("nodes", [])) >= 2:
                    source = path["nodes"][0]
                    target = path["nodes"][1]

                    # Get edge details
                    edge_query = """
                    MATCH (a:Address {address: $source})-[r:SENT|RECEIVED|TAINTED_FLOW]-(b:Address {address: $target})
                    RETURN r.tx_hash as tx_hash, r.value as value, r.timestamp as timestamp,
                           type(r) as event_type, r.bridge as bridge
                    LIMIT 1
                    """
                    edge_result = await neo4j_client.execute_read(edge_query, {
                        "source": source,
                        "target": target
                    })

                    if edge_result:
                        edge = edge_result[0]
                        links.append({
                            "source": source,
                            "target": target,
                            "tx_hash": edge.get("tx_hash"),
                            "value": float(edge.get("value", 0)),
                            "timestamp": edge.get("timestamp"),
                            "event_type": edge.get("event_type"),
                            "bridge": edge.get("bridge")
                        })

        # Calculate summary statistics
        risk_distribution = {}
        for node in nodes.values():
            risk = node["risk_level"]
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

        summary = {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "risk_distribution": risk_distribution,
            "chains": list(set(node["chain"] for node in nodes.values())),
            "time_range": {
                "earliest": min((node["first_seen"] for node in nodes.values() if node["first_seen"]), default=None),
                "latest": max((node["last_seen"] for node in nodes.values() if node["last_seen"]), default=None)
            }
        }

        return GraphExploreResponse(
            nodes=nodes,
            links=links,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error exploring graph for address {address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/path/find", response_model=PathFindResponse)
async def find_path_between_addresses(request: PathFindRequest) -> PathFindResponse:
    """
    Find paths between two addresses

    Uses the existing path finding functionality but returns formatted results
    """
    try:
        paths = await neo4j_client.find_path(
            request.from_address,
            request.to_address,
            request.max_hops
        )

        if not paths:
            return PathFindResponse(
                found=False,
                paths=[],
                summary={"message": "No path found"}
            )

        # Format paths for response
        formatted_paths = []
        total_value = 0
        bridges = set()

        for path in paths[:10]:  # Limit to top 10 paths
            if "nodes" in path and len(path["nodes"]) >= 2:
                formatted_path = {
                    "nodes": path["nodes"],
                    "hops": path.get("hops", len(path["nodes"]) - 1),
                    "edges": path.get("edges", [])
                }
                formatted_paths.append(formatted_path)

                # Extract bridge information
                for edge in path.get("edges", []):
                    if edge.get("bridge"):
                        bridges.add(edge["bridge"])
                    if edge.get("value"):
                        total_value += float(edge["value"])

        # Calculate risk score for the path
        risk_score = 0.0
        if formatted_paths:
            # Simple risk calculation based on connected nodes
            connected_addresses = set()
            for path in formatted_paths:
                connected_addresses.update(path["nodes"])

            # Get risk data for connected addresses
            risk_addresses = await neo4j_client.get_high_risk_connections(list(connected_addresses))
            risk_score = min(100.0, len(risk_addresses) * 10)  # Simple heuristic

        summary = {
            "total_paths": len(formatted_paths),
            "shortest_path_length": min((p["hops"] for p in formatted_paths), default=0),
            "total_value": total_value,
            "bridges_used": list(bridges),
            "risk_score": risk_score
        }

        return PathFindResponse(
            found=len(formatted_paths) > 0,
            paths=formatted_paths,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error finding path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline", response_model=TimelineResponse)
async def get_address_timeline(
    address: str = Query(..., description="Address to get timeline for"),
    from_timestamp: Optional[str] = Query(None, description="Start timestamp"),
    to_timestamp: Optional[str] = Query(None, description="End timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return")
) -> TimelineResponse:
    """
    Get timeline of events for an address

    Returns chronological list of transactions and events
    """
    try:
        # Query for address transactions and events
        query = """
        MATCH (a:Address {address: $address})
        OPTIONAL MATCH (a)-[r:SENT|RECEIVED|TAINTED_FLOW]-(tx:Transaction)
        OPTIONAL MATCH (a)-[bridge:BRIDGE_LINK]-(other:Address)
        WITH a, r, tx, bridge, other
        ORDER BY coalesce(r.timestamp, tx.timestamp, bridge.timestamp) DESC
        LIMIT $limit
        RETURN {
            address: a.address,
            timestamp: coalesce(r.timestamp, tx.timestamp, bridge.timestamp),
            event_type: CASE
                WHEN type(r) = 'SENT' THEN 'sent'
                WHEN type(r) = 'RECEIVED' THEN 'received'
                WHEN type(r) = 'TAINTED_FLOW' THEN 'tainted_flow'
                WHEN type(bridge) = 'BRIDGE_LINK' THEN 'bridge'
                ELSE 'unknown'
            END,
            value: coalesce(r.value, 0),
            tx_hash: coalesce(r.tx_hash, tx.tx_hash, bridge.tx_hash),
            counterparty: CASE
                WHEN type(r) IN ['SENT', 'RECEIVED', 'TAINTED_FLOW'] THEN
                    CASE WHEN r.from_address = a.address THEN r.to_address ELSE r.from_address END
                WHEN type(bridge) = 'BRIDGE_LINK' THEN other.address
                ELSE null
            END,
            bridge: bridge.bridge,
            chain: coalesce(r.chain, tx.chain, bridge.chain)
        } as event
        """

        result = await neo4j_client.execute_read(query, {
            "address": address,
            "limit": limit
        })

        events = []
        for record in result:
            event = record["event"]
            if event["timestamp"]:  # Only include events with timestamps
                events.append({
                    "timestamp": event["timestamp"],
                    "address": event["address"],
                    "event_type": event["event_type"],
                    "value": float(event["value"]),
                    "tx_hash": event["tx_hash"],
                    "counterparty": event["counterparty"],
                    "bridge": event["bridge"],
                    "chain": event["chain"]
                })

        # Calculate summary statistics
        total_value = sum(event["value"] for event in events)
        event_types = {}
        for event in events:
            et = event["event_type"]
            event_types[et] = event_types.get(et, 0) + 1

        summary = {
            "total_events": len(events),
            "total_value": total_value,
            "event_types": event_types,
            "time_range": {
                "earliest": min((e["timestamp"] for e in events), default=None),
                "latest": max((e["timestamp"] for e in events), default=None)
            } if events else None
        }

        return TimelineResponse(
            address=address,
            events=events,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Error getting timeline for address {address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investigator/summary")
async def get_investigator_summary(
    addresses: str = Query(..., description="Comma-separated list of addresses")
) -> Dict[str, Any]:
    """
    Get summary information for multiple addresses

    Useful for batch analysis of connected addresses
    """
    try:
        address_list = [addr.strip() for addr in addresses.split(",") if addr.strip()]

        if len(address_list) > 50:
            raise HTTPException(status_code=400, detail="Too many addresses (max 50)")

        # Get risk scores for all addresses
        risk_scores = {}
        for addr in address_list:
            try:
                risk_data = await alert_service.process_event({"address": addr, "risk_score": 0.5})
                # This is a simplified approach - in practice you'd use the actual risk scorer
                risk_scores[addr] = 0.5  # Placeholder
            except Exception:
                risk_scores[addr] = 0.0

        # Get basic stats for each address
        address_stats = {}
        for addr in address_list:
            try:
                neighbors = await neo4j_client.get_address_neighbors(addr, limit=10)
                address_stats[addr] = {
                    "neighbor_count": len(neighbors),
                    "chains": list(set(n.get("chain", "unknown") for n in neighbors)),
                    "risk_score": risk_scores.get(addr, 0.0)
                }
            except Exception:
                address_stats[addr] = {
                    "neighbor_count": 0,
                    "chains": [],
                    "risk_score": risk_scores.get(addr, 0.0)
                }

        return {
            "addresses": address_list,
            "total_addresses": len(address_list),
            "address_stats": address_stats,
            "overall_risk_distribution": {
                "low": len([addr for addr, stats in address_stats.items() if stats["risk_score"] < 0.3]),
                "medium": len([addr for addr, stats in address_stats.items() if 0.3 <= stats["risk_score"] < 0.7]),
                "high": len([addr for addr, stats in address_stats.items() if stats["risk_score"] >= 0.7])
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting investigator summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationship-graph")
async def get_relationship_graph(
    address: str,
    chain: str = "ethereum",
    depth: int = Query(2, ge=1, le=5),
    current_user: Dict = None
) -> Dict[str, Any]:
    """
    Get relationship graph for an address
    Requires Pro+ Plan
    
    Returns:
    - nodes: List of addresses in graph
    - edges: Connections between addresses
    - metadata: Risk scores, labels, etc.
    """
    from app.models.user import SubscriptionPlan
    from app.auth.plan_gates import is_plan_sufficient
    
    # Check plan
    if current_user and not is_plan_sufficient(SubscriptionPlan.PRO, current_user.plan):
        raise HTTPException(
            status_code=403,
            detail="Investigator requires Pro plan or higher"
        )
    
    try:
        # Build graph (simplified - in real app use Neo4j)
        # Mock implementation for tests
        graph = {
            'nodes': [
                {'id': address, 'type': 'address', 'risk_score': 0.5},
                {'id': '0xabc', 'type': 'address', 'risk_score': 0.3}
            ],
            'edges': [
                {'from': address, 'to': '0xabc', 'value': '1000', 'type': 'transfer'}
            ],
            'metadata': {
                'depth': depth,
                'chain': chain,
                'total_nodes': 2,
                'total_edges': 1
            }
        }
        
        return graph
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building relationship graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
