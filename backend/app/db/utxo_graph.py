"""
UTXO Graph Persistence for Neo4j
Handles Bitcoin UTXO graph structure with :SPENT and :OWNS edges
"""

from typing import Dict, Any, List, Optional
from app.db.neo4j_client import Neo4jClient
from app.schemas import CanonicalEvent


class UTXOGraph:
    """
    Manages UTXO graph structure in Neo4j for Bitcoin transactions.
    
    Graph Structure:
    - (:Address) nodes represent Bitcoin addresses
    - (:UTXO) nodes represent unspent transaction outputs
    - [:SPENT] edges track UTXO consumption (input -> output)
    - [:OWNS] edges link addresses to UTXOs
    - [:CO_SPEND] edges indicate addresses used together (clustering evidence)
    """
    
    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        self.neo4j = neo4j_client or Neo4jClient()
    
    async def save_bitcoin_transaction(self, event: CanonicalEvent) -> Dict[str, Any]:
        """
        Persist a Bitcoin transaction as UTXO graph edges.
        
        Creates:
        1. Address nodes for inputs and outputs
        2. UTXO nodes for each output
        3. SPENT edges from inputs to outputs
        4. OWNS edges from addresses to UTXOs
        5. CO_SPEND edges between co-spending addresses
        """
        if event.chain != "bitcoin":
            raise ValueError(f"Expected bitcoin event, got {event.chain}")
        
        btc_meta = event.metadata.get("bitcoin", {})
        inputs = btc_meta.get("inputs", [])
        outputs = btc_meta.get("outputs", [])
        co_spend_addrs = btc_meta.get("co_spend_addresses", [])
        is_coinjoin = btc_meta.get("is_coinjoin", False)
        change_vout = btc_meta.get("change_vout")
        
        # Cypher queries
        queries = []
        
        # 1. Create address nodes and OWNS edges for outputs
        for output in outputs:
            n = output["n"]
            value = output["value"]
            addresses = output["addresses"]
            output_type = output.get("type", "unknown")
            
            for addr in addresses:
                # Create Address node
                queries.append({
                    "query": """
                        MERGE (a:Address {address: $address, chain: 'bitcoin'})
                        ON CREATE SET a.created_at = datetime()
                        SET a.last_seen = datetime()
                    """,
                    "params": {"address": addr}
                })
                
                # Create UTXO node
                utxo_id = f"{event.tx_hash}:{n}"
                queries.append({
                    "query": """
                        MERGE (u:UTXO {
                            utxo_id: $utxo_id,
                            chain: 'bitcoin'
                        })
                        SET u.txid = $txid,
                            u.vout = $vout,
                            u.value = $value,
                            u.block_number = $block_number,
                            u.timestamp = $timestamp,
                            u.is_change = $is_change,
                            u.type = $type,
                            u.spent = false
                    """,
                    "params": {
                        "utxo_id": utxo_id,
                        "txid": event.tx_hash,
                        "vout": n,
                        "value": float(value),
                        "block_number": event.block_number,
                        "timestamp": event.block_timestamp.isoformat(),
                        "is_change": (n == change_vout),
                        "type": output_type
                    }
                })
                
                # Create OWNS edge
                queries.append({
                    "query": """
                        MATCH (a:Address {address: $address, chain: 'bitcoin'})
                        MATCH (u:UTXO {utxo_id: $utxo_id})
                        MERGE (a)-[o:OWNS]->(u)
                        SET o.since = $timestamp
                    """,
                    "params": {
                        "address": addr,
                        "utxo_id": utxo_id,
                        "timestamp": event.block_timestamp.isoformat()
                    }
                })
        
        # 2. Create SPENT edges for inputs
        for input_data in inputs:
            prev_txid = input_data.get("txid")
            prev_vout = input_data.get("vout")
            
            if prev_txid and prev_vout is not None:
                prev_utxo_id = f"{prev_txid}:{prev_vout}"
                
                # Mark UTXO as spent
                queries.append({
                    "query": """
                        MATCH (u:UTXO {utxo_id: $utxo_id})
                        SET u.spent = true,
                            u.spent_in_tx = $spent_in_tx,
                            u.spent_at_block = $block_number
                    """,
                    "params": {
                        "utxo_id": prev_utxo_id,
                        "spent_in_tx": event.tx_hash,
                        "block_number": event.block_number
                    }
                })
                
                # Create SPENT edges to each output
                for output in outputs:
                    n = output["n"]
                    out_utxo_id = f"{event.tx_hash}:{n}"
                    
                    # Proportional value flow (simplified)
                    total_output_value = sum(o["value"] for o in outputs)
                    proportion = output["value"] / total_output_value if total_output_value > 0 else 0
                    
                    queries.append({
                        "query": """
                            MATCH (in_utxo:UTXO {utxo_id: $in_utxo_id})
                            MATCH (out_utxo:UTXO {utxo_id: $out_utxo_id})
                            MERGE (in_utxo)-[s:SPENT]->(out_utxo)
                            SET s.tx_hash = $tx_hash,
                                s.block_number = $block_number,
                                s.timestamp = $timestamp,
                                s.proportion = $proportion
                        """,
                        "params": {
                            "in_utxo_id": prev_utxo_id,
                            "out_utxo_id": out_utxo_id,
                            "tx_hash": event.tx_hash,
                            "block_number": event.block_number,
                            "timestamp": event.block_timestamp.isoformat(),
                            "proportion": proportion
                        }
                    })
        
        # 3. Create CO_SPEND edges for clustering (multi-input heuristic)
        if len(co_spend_addrs) > 1:
            for i, addr1 in enumerate(co_spend_addrs):
                for addr2 in co_spend_addrs[i+1:]:
                    queries.append({
                        "query": """
                            MATCH (a1:Address {address: $addr1, chain: 'bitcoin'})
                            MATCH (a2:Address {address: $addr2, chain: 'bitcoin'})
                            MERGE (a1)-[cs:CO_SPEND]-(a2)
                            ON CREATE SET cs.first_seen = $timestamp,
                                         cs.tx_count = 1,
                                         cs.evidence_txs = [$tx_hash]
                            ON MATCH SET cs.last_seen = $timestamp,
                                        cs.tx_count = cs.tx_count + 1,
                                        cs.evidence_txs = cs.evidence_txs + $tx_hash
                        """,
                        "params": {
                            "addr1": addr1,
                            "addr2": addr2,
                            "timestamp": event.block_timestamp.isoformat(),
                            "tx_hash": event.tx_hash
                        }
                    })
        
        # 4. Tag CoinJoin transactions
        if is_coinjoin:
            for output in outputs:
                for addr in output["addresses"]:
                    queries.append({
                        "query": """
                            MATCH (a:Address {address: $address, chain: 'bitcoin'})
                            SET a.has_coinjoin = true
                            WITH a
                            MATCH (a)-[:OWNS]->(u:UTXO {txid: $txid})
                            SET u.is_coinjoin = true
                        """,
                        "params": {
                            "address": addr,
                            "txid": event.tx_hash
                        }
                    })
        
        # Execute all queries in a transaction
        results = await self.neo4j.execute_write_batch(queries)
        
        return {
            "tx_hash": event.tx_hash,
            "queries_executed": len(queries),
            "inputs_processed": len(inputs),
            "outputs_created": len(outputs),
            "co_spend_edges": len(co_spend_addrs) * (len(co_spend_addrs) - 1) // 2,
            "is_coinjoin": is_coinjoin
        }
    
    async def get_utxo_history(self, utxo_id: str) -> Dict[str, Any]:
        """
        Get the spending history of a UTXO.
        Returns the chain of UTXOs it was spent to.
        """
        query = """
            MATCH path = (u:UTXO {utxo_id: $utxo_id})-[:SPENT*]->(next:UTXO)
            RETURN path
            LIMIT 100
        """
        
        result = await self.neo4j.execute_read(query, {"utxo_id": utxo_id})
        
        return {
            "utxo_id": utxo_id,
            "spending_chain": [record["path"] for record in result]
        }
    
    async def find_clustered_addresses(self, address: str, min_tx_count: int = 2) -> List[str]:
        """
        Find addresses clustered with the given address via CO_SPEND edges.
        Returns addresses that have co-spent with this address at least min_tx_count times.
        """
        query = """
            MATCH (a:Address {address: $address, chain: 'bitcoin'})-[cs:CO_SPEND]-(other:Address)
            WHERE cs.tx_count >= $min_tx_count
            RETURN other.address as address, cs.tx_count as tx_count
            ORDER BY cs.tx_count DESC
        """
        
        result = await self.neo4j.execute_read(query, {
            "address": address,
            "min_tx_count": min_tx_count
        })
        
        return [record["address"] for record in result]
    
    async def get_address_utxos(self, address: str, spent: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get all UTXOs owned by an address.
        If spent=True, returns only spent UTXOs.
        If spent=False, returns only unspent UTXOs.
        If spent=None, returns all UTXOs.
        """
        if spent is None:
            spent_filter = ""
        elif spent:
            spent_filter = "AND u.spent = true"
        else:
            spent_filter = "AND u.spent = false"
        
        query = f"""
            MATCH (a:Address {{address: $address, chain: 'bitcoin'}})-[:OWNS]->(u:UTXO)
            WHERE 1=1 {spent_filter}
            RETURN u.utxo_id as utxo_id,
                   u.txid as txid,
                   u.vout as vout,
                   u.value as value,
                   u.spent as spent,
                   u.is_change as is_change,
                   u.is_coinjoin as is_coinjoin,
                   u.timestamp as timestamp
            ORDER BY u.block_number DESC
        """
        
        result = await self.neo4j.execute_read(query, {"address": address})
        
        return [dict(record) for record in result]
    
    async def trace_utxo_flow(
        self,
        start_utxo_id: str,
        max_hops: int = 10
    ) -> Dict[str, Any]:
        """
        Trace the flow of value from a UTXO through the SPENT graph.
        Returns a subgraph of UTXO nodes and SPENT edges.
        """
        query = """
            MATCH path = (start:UTXO {utxo_id: $utxo_id})-[:SPENT*1..$max_hops]->(end:UTXO)
            WITH path, length(path) as depth
            RETURN 
                [n in nodes(path) | {
                    utxo_id: n.utxo_id,
                    txid: n.txid,
                    vout: n.vout,
                    value: n.value,
                    spent: n.spent
                }] as nodes,
                [r in relationships(path) | {
                    from: startNode(r).utxo_id,
                    to: endNode(r).utxo_id,
                    tx_hash: r.tx_hash,
                    proportion: r.proportion
                }] as edges,
                depth
            ORDER BY depth
            LIMIT 1000
        """
        
        result = await self.neo4j.execute_read(query, {
            "utxo_id": start_utxo_id,
            "max_hops": max_hops
        })
        
        all_nodes = []
        all_edges = []
        
        for record in result:
            all_nodes.extend(record["nodes"])
            all_edges.extend(record["edges"])
        
        # Deduplicate
        unique_nodes = {n["utxo_id"]: n for n in all_nodes}
        unique_edges = []
        edge_set = set()
        
        for e in all_edges:
            key = (e["from"], e["to"])
            if key not in edge_set:
                edge_set.add(key)
                unique_edges.append(e)
        
        return {
            "start_utxo": start_utxo_id,
            "max_hops": max_hops,
            "nodes": list(unique_nodes.values()),
            "edges": unique_edges,
            "total_paths": len(result)
        }
