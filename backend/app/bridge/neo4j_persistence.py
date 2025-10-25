"""
Neo4j Persistence for Bridge Links
Handles :BRIDGE_LINK edge creation and cross-chain graph connections
"""

import logging
from typing import Dict, List, Any

from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class BridgePersistence:
    """
    Handles persistence of bridge transactions as :BRIDGE_LINK edges in Neo4j.
    
    Graph Structure:
    - (:Address {chain: "ethereum"})-[:BRIDGE_LINK {chain_from, chain_to, bridge, ...}]->(:Address {chain: "polygon"})
    
    Features:
    - Automatic address node creation
    - Cross-chain edge creation
    - Bridge metadata persistence
    - Query helpers for bridge analysis
    """
    
    def __init__(self):
        self.neo4j = neo4j_client
    
    async def save_bridge_link(
        self,
        from_address: str,
        to_address: str,
        bridge_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Persist a bridge link as a Neo4j :BRIDGE_LINK edge.
        
        Args:
            from_address: Source address on source chain
            to_address: Destination address on destination chain
            bridge_info: Bridge metadata dict
            
        Returns:
            Result dict with stats
        """
        try:
            chain_from = bridge_info.get("source_chain", "unknown")
            chain_to = bridge_info.get("destination_chain", "unknown")
            
            query = """
                // Create or merge source address node
                MERGE (from:Address {address: $from_address, chain: $chain_from})
                ON CREATE SET from.created_at = datetime()
                SET from.last_seen = datetime()
                
                // Create or merge destination address node
                MERGE (to:Address {address: $to_address, chain: $chain_to})
                ON CREATE SET to.created_at = datetime()
                SET to.last_seen = datetime()
                
                // Create BRIDGE_LINK edge
                MERGE (from)-[b:BRIDGE_LINK {
                    tx_hash: $tx_hash,
                    chain_from: $chain_from,
                    chain_to: $chain_to
                }]->(to)
                ON CREATE SET
                    b.bridge = $bridge_name,
                    b.bridge_contract = $bridge_contract,
                    b.timestamp = $timestamp,
                    b.value = $value,
                    b.token_address = $token_address,
                    b.token_symbol = $token_symbol,
                    b.bridge_type = $bridge_type,
                    b.created_at = datetime()
                ON MATCH SET
                    b.last_seen = datetime()
                
                RETURN id(b) as edge_id
            """
            
            params = {
                "from_address": from_address.lower(),
                "to_address": to_address.lower(),
                "chain_from": chain_from,
                "chain_to": chain_to,
                "tx_hash": bridge_info.get("tx_hash"),
                "bridge_name": bridge_info.get("bridge_name", "unknown"),
                "bridge_contract": bridge_info.get("bridge_contract", ""),
                "timestamp": bridge_info.get("timestamp"),
                "value": str(bridge_info.get("value", 0)),
                "token_address": bridge_info.get("token_address"),
                "token_symbol": bridge_info.get("token_symbol"),
                "bridge_type": bridge_info.get("bridge_type", "unknown"),
            }
            
            result = await self.neo4j.execute_write(query, params)
            
            logger.info(
                f"Saved bridge link: {from_address} ({chain_from}) -> "
                f"{to_address} ({chain_to}) via {bridge_info.get('bridge_name')}"
            )
            
            return {
                "success": True,
                "edge_id": result[0]["edge_id"] if result else None,
                "from_address": from_address,
                "to_address": to_address,
                "chain_from": chain_from,
                "chain_to": chain_to,
            }
        
        except Exception as e:
            logger.error(f"Failed to save bridge link: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_bridge_links_for_address(
        self,
        address: str,
        direction: str = "both",  # "outgoing", "incoming", "both"
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all bridge links for an address.
        
        Args:
            address: Address to query
            direction: Link direction to query
            limit: Max results
            
        Returns:
            List of bridge link dicts
        """
        try:
            if direction == "outgoing":
                pattern = "(a:Address {address: $address})-[b:BRIDGE_LINK]->(dest:Address)"
            elif direction == "incoming":
                pattern = "(source:Address)-[b:BRIDGE_LINK]->(a:Address {address: $address})"
            else:  # both
                pattern = """
                    (a:Address {address: $address})-[b:BRIDGE_LINK]-(other:Address)
                """
            
            query = f"""
                MATCH {pattern}
                RETURN b.chain_from AS chain_from,
                       b.chain_to AS chain_to,
                       b.bridge AS bridge_name,
                       b.tx_hash AS tx_hash,
                       b.timestamp AS timestamp,
                       b.value AS value,
                       b.token_symbol AS token_symbol,
                       CASE 
                           WHEN direction == "outgoing" THEN dest.address
                           WHEN direction == "incoming" THEN source.address
                           ELSE other.address
                       END AS counterpart_address
                ORDER BY b.timestamp DESC
                LIMIT $limit
            """
            
            result = await self.neo4j.execute_read(query, {
                "address": address.lower(),
                "limit": limit
            })
            
            return [dict(record) for record in result]
        
        except Exception as e:
            logger.error(f"Failed to get bridge links for {address}: {e}")
            return []
    
    async def get_cross_chain_path(
        self,
        start_address: str,
        start_chain: str,
        end_chain: str,
        max_hops: int = 5
    ) -> List[List[Dict[str, Any]]]:
        """
        Find cross-chain paths from start_address to end_chain.
        
        Args:
            start_address: Starting address
            start_chain: Starting chain
            end_chain: Target chain
            max_hops: Maximum bridge hops
            
        Returns:
            List of paths (each path is list of bridge links)
        """
        try:
            query = """
                MATCH path = (start:Address {address: $start_address, chain: $start_chain})
                             -[:BRIDGE_LINK*1..$max_hops]->
                             (end:Address {chain: $end_chain})
                WITH path, length(path) as hop_count
                ORDER BY hop_count ASC
                LIMIT 10
                RETURN [rel in relationships(path) | {
                    chain_from: rel.chain_from,
                    chain_to: rel.chain_to,
                    bridge: rel.bridge,
                    tx_hash: rel.tx_hash,
                    timestamp: rel.timestamp
                }] as bridge_path,
                hop_count
            """
            
            result = await self.neo4j.execute_read(query, {
                "start_address": start_address.lower(),
                "start_chain": start_chain,
                "end_chain": end_chain,
                "max_hops": max_hops
            })
            
            paths = []
            for record in result:
                paths.append({
                    "path": record["bridge_path"],
                    "hops": record["hop_count"]
                })
            
            return paths
        
        except Exception as e:
            logger.error(f"Failed to find cross-chain path: {e}")
            return []
    
    async def get_bridge_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about bridge usage.
        
        Returns:
            Dict with bridge stats
        """
        try:
            query = """
                MATCH ()-[b:BRIDGE_LINK]->()
                WITH b.bridge AS bridge_name,
                     b.chain_from AS chain_from,
                     b.chain_to AS chain_to,
                     count(*) AS tx_count,
                     sum(toFloat(b.value)) AS total_value
                RETURN bridge_name,
                       chain_from,
                       chain_to,
                       tx_count,
                       total_value
                ORDER BY tx_count DESC
            """
            
            result = await self.neo4j.execute_read(query, {})
            
            total_txs = sum(r.get("tx_count", 0) for r in result)
            
            return {
                "total_bridge_transactions": total_txs,
                "bridge_breakdown": [dict(r) for r in result],
            }
        
        except Exception as e:
            logger.error(f"Failed to get bridge statistics: {e}")
            return {
                "total_bridge_transactions": 0,
                "bridge_breakdown": [],
            }
    
    async def find_linked_addresses_cross_chain(
        self,
        address: str,
        source_chain: str,
        target_chain: str
    ) -> List[str]:
        """
        Find all addresses on target_chain linked to address on source_chain.
        
        Forensic use case: Find Polygon addresses linked to Ethereum address.
        
        Args:
            address: Source address
            source_chain: Source chain
            target_chain: Target chain to find links
            
        Returns:
            List of linked addresses on target chain
        """
        try:
            query = """
                MATCH (source:Address {address: $address, chain: $source_chain})
                      -[:BRIDGE_LINK*1..3]->
                      (target:Address {chain: $target_chain})
                RETURN DISTINCT target.address AS linked_address
                LIMIT 100
            """
            
            result = await self.neo4j.execute_read(query, {
                "address": address.lower(),
                "source_chain": source_chain,
                "target_chain": target_chain
            })
            
            return [r["linked_address"] for r in result]
        
        except Exception as e:
            logger.error(f"Failed to find linked addresses: {e}")
            return []


# Global instance
bridge_persistence = BridgePersistence()
