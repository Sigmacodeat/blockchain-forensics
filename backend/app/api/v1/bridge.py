"""
Bridge Analytics API Endpoints
===============================

Forensic-Grade Cross-Chain Bridge Analysis
- Bridge Detection & Classification
- Cross-Chain Transaction Linking  
- Bridge Flow Analysis (Multi-Hop Tracing)
- Gerichtsverwertbare Bridge Reports
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.bridge.registry import bridge_registry, BridgeContract
from app.bridge.detection import bridge_detection_service
from app.schemas.canonical_event import CanonicalEvent
from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Request/Response Models =====

class BridgeDetectionRequest(BaseModel):
    """Request to detect bridge in a transaction"""
    tx_hash: str = Field(..., description="Transaction hash")
    chain: str = Field(..., description="Source chain (ethereum, solana, polygon, etc.)")


class BridgeFlowRequest(BaseModel):
    """Request to analyze bridge flow for an address"""
    address: str = Field(..., description="Address to analyze")
    max_hops: int = Field(5, ge=1, le=10, description="Maximum bridge hops to trace")


class BridgeDetectionResponse(BaseModel):
    """Response with bridge detection results"""
    is_bridge: bool
    bridge_data: Optional[Dict] = None


class BridgeFlowResponse(BaseModel):
    """Response with bridge flow analysis"""
    address: str
    total_flows: int
    max_hops_found: int
    flows: List[Dict]
    analysis_timestamp: str


class BridgeRegistryResponse(BaseModel):
    """Response with bridge registry info"""
    total_bridges: int
    supported_chains: List[str]
    bridges: List[Dict]


class BridgeStatsResponse(BaseModel):
    """Response with bridge usage statistics"""
    total_bridge_transactions: int
    unique_addresses: int
    top_bridges: List[Dict]
    chain_distribution: Dict[str, int]


# ===== API Endpoints =====

@router.get("/supported-bridges", response_model=BridgeRegistryResponse)
async def get_supported_bridges(
    chain: Optional[str] = Query(None, description="Filter by chain")
) -> BridgeRegistryResponse:
    """
    Get list of all supported bridges
    
    Returns registry of 10+ major bridges with detection signatures
    """
    try:
        # Fetch contracts from registry
        contracts = bridge_registry.get_all_contracts()
        if chain:
            contracts = [c for c in contracts if c.chain.lower() == chain.lower()]

        bridges_data = [
            {
                "bridge_name": c.name,
                "chain": c.chain,
                "contract_count": 1,
                "pattern_type": c.bridge_type,
                "metadata": {
                    "counterpart_chains": c.counterpart_chains,
                    "method_selectors": c.method_selectors,
                    "address": c.address,
                },
            }
            for c in contracts
        ]

        chains = sorted(list({c.chain for c in contracts}))

        return BridgeRegistryResponse(
            total_bridges=len(bridges_data),
            supported_chains=chains,
            bridges=bridges_data,
        )
    
    except Exception as e:
        logger.error(f"Failed to get bridge registry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bridge registry: {e}")


@router.post("/detect", response_model=BridgeDetectionResponse)
async def detect_bridge_transaction(request: BridgeDetectionRequest) -> BridgeDetectionResponse:
    """
    Detect if a transaction is a bridge interaction
    
    Analyzes transaction and returns bridge metadata if detected
    """
    try:
        chain = request.chain.lower()
        tx_hash = request.tx_hash

        # Prefer native EVM adapter for EVM chains to build a CanonicalEvent
        if chain in {"ethereum", "polygon", "bsc", "arbitrum", "optimism"}:
            try:
                # Lazy import to avoid heavy deps if unused
                from app.adapters.ethereum_adapter import EthereumAdapter  # type: ignore
                evm = EthereumAdapter()
                raw_tx = await evm.get_transaction(tx_hash)
                if not raw_tx:
                    raise HTTPException(status_code=404, detail="Transaction not found")
                receipt = await evm.get_transaction_receipt(tx_hash)
                block_num = int(raw_tx.get("blockNumber", 0))
                block_data = await evm.get_block(block_num)
                event: CanonicalEvent = await evm.transform_transaction(raw_tx, block_data)
                # Detect using BridgeDetectionService and persist if possible
                bridge = bridge_detection_service.detect_bridge_transaction(event, raw_tx)
                if bridge:
                    edge = bridge_detection_service.create_bridge_link_data(bridge)
                    try:
                        bridge_detection_service.persist_bridge_link(
                            bridge.get("from_address") or event.from_address,
                            bridge.get("to_address") or event.to_address or "",
                            edge,
                        )
                    except Exception:
                        pass
                return BridgeDetectionResponse(
                    is_bridge=bool(bridge),
                    bridge_data=bridge,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"EVM detect fallback due to error: {e}")

        # Solana support: use SolanaAdapter to fetch and build CanonicalEvent
        if chain == "solana":
            try:
                from app.adapters.solana_adapter import create_solana_adapter  # type: ignore
                sol = create_solana_adapter()
                raw_tx = await sol.get_transaction(tx_hash)
                if not raw_tx:
                    raise HTTPException(status_code=404, detail="Transaction not found")
                # On Solana we already have a canonical event builder
                event: CanonicalEvent = await sol.to_canonical(raw_tx)
                bridge = bridge_detection_service.detect_bridge_transaction(event, raw_tx)
                if bridge:
                    edge = bridge_detection_service.create_bridge_link_data(bridge)
                    try:
                        bridge_detection_service.persist_bridge_link(
                            bridge.get("from_address") or event.from_address,
                            bridge.get("to_address") or event.to_address or "",
                            edge,
                        )
                    except Exception:
                        pass
                return BridgeDetectionResponse(
                    is_bridge=bool(bridge),
                    bridge_data=bridge,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Solana detect fallback due to error: {e}")

        # Fallback: No EVM or non‑EVM chain – return non‑bridge for now
        return BridgeDetectionResponse(is_bridge=False, bridge_data=None)
    
    except Exception as e:
        logger.error(f"Bridge detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bridge detection failed: {e}")


@router.post("/flow-analysis", response_model=BridgeFlowResponse)
async def analyze_bridge_flow(request: BridgeFlowRequest) -> BridgeFlowResponse:
    """
    Analyze cross-chain bridge flow for an address
    
    Traces multi-hop bridge transactions and maps cross-chain movements
    """
    try:
        # Use BridgeDetectionService for flow-analysis (Neo4j-based)
        analysis = bridge_detection_service.analyze_bridge_flow(
            address=request.address,
            max_hops=request.max_hops,
        )
        return BridgeFlowResponse(**analysis)
    
    except Exception as e:
        logger.error(f"Bridge flow analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bridge flow analysis failed: {e}")


@router.get("/statistics", response_model=BridgeStatsResponse)
async def get_bridge_statistics() -> BridgeStatsResponse:
    """
    Get bridge usage statistics from Neo4j
    
    Returns:
    - Total bridge transactions
    - Unique addresses using bridges
    - Top bridges by volume
    - Chain distribution
    """
    try:
        # Query Neo4j for bridge statistics
        stats_query = """
        MATCH ()-[r:BRIDGE_LINK]->()
        WITH r.bridge AS bridge_name, 
             r.chain_from AS chain_from,
             r.chain_to AS chain_to,
             count(*) AS tx_count
        RETURN bridge_name, chain_from, chain_to, tx_count
        ORDER BY tx_count DESC
        """
        
        results = await neo4j_client.query(stats_query, {})
        
        # Aggregate statistics
        total_txs = sum(r.get("tx_count", 0) for r in results)
        
        # Top bridges
        top_bridges = [
            {
                "bridge_name": r["bridge_name"],
                "chain_from": r["chain_from"],
                "chain_to": r["chain_to"],
                "transaction_count": r["tx_count"],
            }
            for r in results[:10]  # Top 10
        ]
        
        # Chain distribution
        chain_dist = {}
        for r in results:
            chain_from = r["chain_from"]
            chain_dist[chain_from] = chain_dist.get(chain_from, 0) + r["tx_count"]
        
        # Unique addresses (separate query)
        unique_query = """
        MATCH (a:Address)-[:BRIDGE_LINK]->()
        RETURN count(DISTINCT a) AS unique_count
        """
        unique_result = await neo4j_client.query(unique_query, {})
        unique_count = unique_result[0].get("unique_count", 0) if unique_result else 0
        
        return BridgeStatsResponse(
            total_bridge_transactions=total_txs,
            unique_addresses=unique_count,
            top_bridges=top_bridges,
            chain_distribution=chain_dist,
        )
    
    except Exception as e:
        logger.error(f"Failed to get bridge statistics: {e}")
        # Return empty stats on error
        return BridgeStatsResponse(
            total_bridge_transactions=0,
            unique_addresses=0,
            top_bridges=[],
            chain_distribution={},
        )


@router.get("/address/{address}/bridges")
async def get_address_bridge_history(
    address: str,
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
) -> Dict:
    """
    Get bridge transaction history for a specific address
    
    Returns all bridge interactions for the address across all chains
    """
    try:
        query = """
        MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]->(dest:Address)
        RETURN r.bridge AS bridge_name,
               r.chain_from AS chain_from,
               r.chain_to AS chain_to,
               r.tx_hash AS tx_hash,
               r.timestamp AS timestamp,
               dest.address AS destination_address
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        
        results = await neo4j_client.query(
            query, 
            {"address": address.lower(), "limit": limit}
        )
        
        bridges = [
            {
                "bridge_name": r["bridge_name"],
                "chain_from": r["chain_from"],
                "chain_to": r["chain_to"],
                "tx_hash": r["tx_hash"],
                "timestamp": r["timestamp"],
                "destination_address": r["destination_address"],
            }
            for r in results
        ]
        
        return {
            "address": address,
            "total_bridge_transactions": len(bridges),
            "bridges": bridges,
        }
    
    except Exception as e:
        logger.error(f"Failed to get address bridge history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bridge history: {e}")


@router.get("/cross-chain-link")
async def find_cross_chain_link(
    source_address: str = Query(..., description="Source address on chain A"),
    source_chain: str = Query(..., description="Source chain (ethereum, solana, etc.)"),
    target_chain: str = Query(..., description="Target chain to search"),
) -> Dict:
    """
    Find linked address on target chain via bridge
    
    Forensic use case: Given address on Ethereum, find Solana address
    """
    try:
        query = """
        MATCH (source:Address {address: $source_address})-[r:BRIDGE_LINK]->(dest:Address)
        WHERE r.chain_from = $source_chain 
          AND r.chain_to = $target_chain
        RETURN dest.address AS linked_address,
               r.bridge AS bridge_name,
               r.tx_hash AS tx_hash,
               r.timestamp AS timestamp
        ORDER BY r.timestamp DESC
        LIMIT 10
        """
        
        results = await neo4j_client.query(query, {
            "source_address": source_address.lower(),
            "source_chain": source_chain.lower(),
            "target_chain": target_chain.lower(),
        })
        
        links = [
            {
                "linked_address": r["linked_address"],
                "bridge_name": r["bridge_name"],
                "tx_hash": r["tx_hash"],
                "timestamp": r["timestamp"],
            }
            for r in results
        ]
        
        return {
            "source_address": source_address,
            "source_chain": source_chain,
            "target_chain": target_chain,
            "found_links": len(links),
            "links": links,
        }
    
    except Exception as e:
        logger.error(f"Failed to find cross-chain link: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find cross-chain link: {e}")


@router.get("/health")
async def bridge_health() -> Dict:
    """Health check for bridge detection service"""
    try:
        stats = bridge_registry.get_stats()
        
        return {
            "status": "healthy",
            "registered_bridges": stats["total_contracts"],
            "supported_chains": stats["total_chains"],
            "total_selectors": stats["total_selectors"],
            "detector_active": True,
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
        }


# ===== New Registry Management Endpoints =====

@router.get("/registry", response_model=Dict)
async def get_registry_info(
    chain: Optional[str] = Query(None, description="Filter by chain")
) -> Dict:
    """
    Get bridge registry information
    
    Returns all registered bridge contracts with metadata
    """
    try:
        if chain:
            contracts = bridge_registry.get_contracts_by_chain(chain)
        else:
            contracts = bridge_registry.get_all_contracts()
        
        contracts_data = [
            {
                "address": c.address,
                "chain": c.chain,
                "name": c.name,
                "bridge_type": c.bridge_type,
                "counterpart_chains": c.counterpart_chains,
                "method_selectors": c.method_selectors,
                "added_at": c.added_at.isoformat() if c.added_at else None,
            }
            for c in contracts
        ]
        
        stats = bridge_registry.get_stats()
        
        return {
            "total_contracts": stats["total_contracts"],
            "total_chains": stats["total_chains"],
            "total_selectors": stats["total_selectors"],
            "contracts": contracts_data,
        }
    
    except Exception as e:
        logger.error(f"Failed to get registry info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get registry: {e}")


class RegisterBridgeRequest(BaseModel):
    """Request to register a new bridge contract"""
    address: str = Field(..., description="Bridge contract address")
    chain: str = Field(..., description="Chain name")
    name: str = Field(..., description="Bridge name")
    bridge_type: str = Field("third_party", description="canonical or third_party")
    counterpart_chains: List[str] = Field(..., description="Chains this bridge connects to")
    method_selectors: List[str] = Field(default_factory=list, description="Method selectors")


@router.post("/registry", response_model=Dict)
async def register_bridge_contract(request: RegisterBridgeRequest) -> Dict:
    """
    Register a new bridge contract (Admin endpoint)
    
    Dynamically add bridge contracts to the registry
    """
    try:
        contract = BridgeContract(
            address=request.address,
            chain=request.chain,
            name=request.name,
            bridge_type=request.bridge_type,
            counterpart_chains=request.counterpart_chains,
            method_selectors=request.method_selectors,
        )
        
        success = bridge_registry.register(contract)
        
        if success:
            return {
                "status": "registered",
                "contract": {
                    "address": contract.address,
                    "chain": contract.chain,
                    "name": contract.name,
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to register contract")
    
    except Exception as e:
        logger.error(f"Failed to register bridge: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@router.delete("/registry/{chain}/{address}", response_model=Dict)
async def remove_bridge_contract(chain: str, address: str) -> Dict:
    """
    Remove a bridge contract from registry (Admin endpoint)
    """
    try:
        success = bridge_registry.remove_contract(address, chain)
        
        if success:
            return {
                "status": "removed",
                "chain": chain,
                "address": address,
            }
        else:
            raise HTTPException(status_code=404, detail="Contract not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove bridge: {e}")
        raise HTTPException(status_code=500, detail=f"Removal failed: {e}")


@router.get("/links", response_model=Dict)
async def get_bridge_links(
    address: Optional[str] = Query(None, description="Filter by address"),
    chain_from: Optional[str] = Query(None, description="Filter by source chain"),
    chain_to: Optional[str] = Query(None, description="Filter by destination chain"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
) -> Dict:
    """
    Get bridge links from the graph
    
    Query :BRIDGE_LINK edges with optional filters
    """
    try:
        # Build dynamic Cypher query
        conditions = []
        params = {"limit": limit}
        
        if address:
            conditions.append("(a.address = $address OR dest.address = $address)")
            params["address"] = address.lower()
        
        if chain_from:
            conditions.append("r.chain_from = $chain_from")
            params["chain_from"] = chain_from.lower()
        
        if chain_to:
            conditions.append("r.chain_to = $chain_to")
            params["chain_to"] = chain_to.lower()
        
        where_clause = " AND ".join(conditions) if conditions else "true"
        
        query = f"""
        MATCH (a:Address)-[r:BRIDGE_LINK]->(dest:Address)
        WHERE {where_clause}
        RETURN a.address AS from_address,
               dest.address AS to_address,
               r.chain_from AS chain_from,
               r.chain_to AS chain_to,
               r.bridge AS bridge_name,
               r.tx_hash AS tx_hash,
               r.timestamp AS timestamp,
               r.value AS value
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        
        results = await neo4j_client.query(query, params)
        
        links = [
            {
                "from_address": r["from_address"],
                "to_address": r["to_address"],
                "chain_from": r["chain_from"],
                "chain_to": r["chain_to"],
                "bridge_name": r["bridge_name"],
                "tx_hash": r["tx_hash"],
                "timestamp": r["timestamp"],
                "value": r["value"],
            }
            for r in results
        ]
        
        return {
            "total_links": len(links),
            "links": links,
        }
    
    except Exception as e:
        logger.error(f"Failed to get bridge links: {e}")
        # Return empty on error (no DB connection)
        return {
            "total_links": 0,
            "links": [],
        }
