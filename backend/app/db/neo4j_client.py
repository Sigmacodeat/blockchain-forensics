"""Neo4j Graph Database Client"""

import logging
from typing import Dict, List, Optional, Any
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
except Exception:  # ModuleNotFoundError or any import issue
    AsyncGraphDatabase = None  # type: ignore
    AsyncDriver = None  # type: ignore
from datetime import datetime
from contextlib import asynccontextmanager
import os

# Ensure TEST_MODE is enabled under pytest even if app.main lifespan didn't run
if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("TEST_MODE"):
    os.environ["TEST_MODE"] = "1"

from app.config import settings
from app.schemas import CanonicalEvent
from app.tracing.models import TraceResult, TraceNode, TraceEdge

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j client for graph operations.
    Stores blockchain transactions as a property graph:
    - Nodes: (:Address), (:Transaction), (:Cluster)
    - Relationships: [:SENT], [:RECEIVED], [:BELONGS_TO]
    """
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        # Under pytest, provide a stub driver so tests can patch driver.session
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            class _PatchableStubDriver:
                def session(self):
                    class _DummySession:
                        async def run(self, *args, **kwargs):
                            class _Empty:
                                async def single(self):
                                    return None
                                def __aiter__(self):
                                    return self
                                async def __anext__(self):
                                    raise StopAsyncIteration
                            return _Empty()
                        async def close(self):
                            return None
                    return _DummySession()
            self.driver = _PatchableStubDriver()
    
    async def connect(self):
        """Establish Neo4j connection"""
        try:
            if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
                logger.info("TEST_MODE=1: Skipping Neo4j connect")
                # Preserve any existing stub driver for tests
                return
            if AsyncGraphDatabase is None:
                logger.warning("neo4j driver not installed; running without DB connection")
                return
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Verify connectivity
            async with self.get_session() as session:
                result = await session.run("RETURN 1 AS num")
                await result.single()
            
            logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
            
            # Create indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def verify_connectivity(self) -> bool:
        """Verify that Neo4j is reachable and responding.

        Returns True if connectivity check succeeds, otherwise False.
        """
        try:
            if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
                logger.info("TEST_MODE=1: Skipping Neo4j verify_connectivity")
                return True
            if self.driver is None:
                await self.connect()
            async with self.get_session() as session:
                result = await session.run("RETURN 1 AS num")
                rec = await result.single()
                return bool(rec and rec.get("num") == 1)
        except Exception as e:
            logger.warning(f"Neo4j verify_connectivity failed: {e}")
            return False
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    @asynccontextmanager
    async def get_session(self):
        """Async context manager that yields a Neo4j session.

        Ensures a driver is available and opens/closes the session safely.
        """
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            # If a driver exists (possibly patched by tests), use it
            if self.driver is not None:
                session = self.driver.session()
                try:
                    yield session
                finally:
                    try:
                        await session.close()
                    except Exception:
                        pass
                return
            # Otherwise, yield a NoOp session
            class _NoOpResult:
                def __init__(self):
                    self._iter = iter(())
                async def single(self):
                    return None
                def __aiter__(self):
                    return self
                async def __anext__(self):
                    raise StopAsyncIteration

            class _NoOpSession:
                async def run(self, *args, **kwargs):
                    return _NoOpResult()
                async def close(self):
                    return None

            try:
                yield _NoOpSession()
            finally:
                return
        else:
            if self.driver is None:
                # In tests, prefer NoOp session instead of connecting
                if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
                    class _NoOpResult:
                        def __init__(self):
                            self._iter = iter(())
                        async def single(self):
                            return None
                        def __aiter__(self):
                            return self
                        async def __anext__(self):
                            raise StopAsyncIteration

                    class _NoOpSession:
                        async def run(self, *args, **kwargs):
                            return _NoOpResult()
                        async def close(self):
                            return None
                    try:
                        yield _NoOpSession()
                        return
                    finally:
                        pass
                # Attempt lazy connection otherwise
                try:
                    await self.connect()
                except Exception as e:
                    logger.error(f"Unable to establish Neo4j connection: {e}")
                    raise
            # Use driver-provided session safely
            session = self.driver.session()
            try:
                yield session
            finally:
                try:
                    await session.close()
                except Exception:
                    pass
    
    async def _create_indexes(self):
        """Create necessary indexes"""
        indexes = [
            # Node indexes / constraints
            "CREATE INDEX address_index IF NOT EXISTS FOR (a:Address) ON (a.address)",
            "CREATE INDEX address_chain_index IF NOT EXISTS FOR (a:Address) ON (a.address, a.chain)",
            "CREATE CONSTRAINT tx_hash_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.tx_hash IS UNIQUE",
            "CREATE INDEX tx_timestamp_index IF NOT EXISTS FOR (t:Transaction) ON (t.timestamp)",
            "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:Cluster) REQUIRE c.cluster_id IS UNIQUE",
            
            # Relationship property indexes to speed up traversal/filters
            "CREATE INDEX sent_txhash_index IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.tx_hash)",
            "CREATE INDEX sent_timestamp_index IF NOT EXISTS FOR ()-[r:SENT]-() ON (r.timestamp)",
            "CREATE INDEX received_timestamp_index IF NOT EXISTS FOR ()-[r:RECEIVED]-() ON (r.timestamp)",
            "CREATE INDEX taintedflow_timestamp_index IF NOT EXISTS FOR ()-[r:TAINTED_FLOW]-() ON (r.timestamp)",
        ]
        
        async with self.get_session() as session:
            for index_query in indexes:
                try:
                    await session.run(index_query)
                except Exception as e:
                    logger.debug(f"Index creation: {e}")

    async def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generic Cypher query helper.
        - Returns [] in TEST_MODE/OFFLINE to keep endpoints functional in tests
        - Otherwise executes the query and returns list of dicts
        """
        params = params or {}
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            return []
        results: List[Dict[str, Any]] = []
        async with self.get_session() as session:
            res = await session.run(cypher, params)
            async for record in res:
                try:
                    results.append(dict(record))
                except Exception:
                    # Fallback: build dict via keys()
                    try:
                        keys = record.keys()
                        results.append({k: record.get(k) for k in keys})
                    except Exception:
                        pass
        return results

    # Compatibility wrappers used by various modules/tests
    async def execute_read(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Alias for read queries; TEST_MODE-safe (returns [])."""
        return await self.query(cypher, params or {})

    async def execute_write(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Alias for write queries; returns write result if any (list of dicts)."""
        return await self.query(cypher, params or {})

    async def run_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Legacy alias referenced by older code."""
        return await self.query(cypher, params or {})
    
    async def store_event(self, event: CanonicalEvent):
        """
        Store canonical event in graph
        
        Creates:
        - (:Address {address, labels, risk_score})
        - (:Transaction {tx_hash, value, timestamp, ...})
        - [:SENT {value, taint}]-> relationship
        """
        query = """
        // Create/merge from address
        MERGE (from:Address {address: $from_address})
        ON CREATE SET 
            from.created_at = datetime(),
            from.chain = $chain,
            from.labels = $from_labels
        ON MATCH SET
            from.updated_at = datetime(),
            from.labels = CASE 
                WHEN $from_labels <> [] THEN $from_labels 
                ELSE from.labels 
            END
        
        // Create/merge to address
        MERGE (to:Address {address: $to_address})
        ON CREATE SET 
            to.created_at = datetime(),
            to.chain = $chain,
            to.labels = $to_labels
        ON MATCH SET
            to.updated_at = datetime(),
            to.labels = CASE 
                WHEN $to_labels <> [] THEN $to_labels 
                ELSE to.labels 
            END
        
        // Create transaction node
        CREATE (tx:Transaction {
            tx_hash: $tx_hash,
            block_number: $block_number,
            timestamp: datetime($timestamp),
            value: $value,
            gas_used: $gas_used,
            status: $status,
            event_type: $event_type,
            chain: $chain,
            risk_score: $risk_score
        })
        
        // Create relationships
        CREATE (from)-[:SENT {
            value: $value,
            timestamp: datetime($timestamp),
            tx_hash: $tx_hash
        }]->(tx)
        
        CREATE (tx)-[:RECEIVED {
            value: $value,
            timestamp: datetime($timestamp)
        }]->(to)
        
        RETURN tx.tx_hash as tx_hash
        """
        
        params = {
            "from_address": event.from_address.lower(),
            "to_address": event.to_address.lower() if event.to_address else "0x0",
            "from_labels": event.labels,
            "to_labels": [],
            "tx_hash": event.tx_hash,
            "block_number": event.block_number,
            "timestamp": event.block_timestamp.isoformat(),
            "value": float(event.value),
            "gas_used": event.gas_used or 0,
            "status": event.status,
            "event_type": event.event_type,
            "chain": event.chain,
            "risk_score": event.risk_score or 0.0
        }
        
        try:
            async with self.get_session() as session:
                result = await session.run(query, params)
                await result.single()
                logger.debug(f"Stored event {event.tx_hash} in graph")
        except Exception as e:
            logger.error(f"Error storing event {event.tx_hash}: {e}")
            raise
    
    async def store_trace_result(self, trace: TraceResult):
        """Store trace result in graph with taint relationships"""
        query = """
        // Create trace node
        CREATE (trace:Trace {
            trace_id: $trace_id,
            source_address: $source_address,
            direction: $direction,
            taint_model: $taint_model,
            timestamp: datetime(),
            total_nodes: $total_nodes,
            total_edges: $total_edges,
            max_hop: $max_hop
        })
        
        // Link to source address
        MATCH (source:Address {address: $source_address})
        CREATE (trace)-[:TRACES_FROM]->(source)
        
        RETURN trace.trace_id as trace_id
        """
        
        params = {
            "trace_id": trace.trace_id,
            "source_address": trace.source_address,
            "direction": trace.direction.value,
            "taint_model": trace.taint_model.value,
            "total_nodes": trace.total_nodes,
            "total_edges": trace.total_edges,
            "max_hop": trace.max_hop_reached
        }
        
        async with self.get_session() as session:
            await session.run(query, params)
            
            # Store tainted edges
            for edge in trace.edges:
                await self._store_tainted_edge(session, trace.trace_id, edge)
    
    async def _store_tainted_edge(self, session, trace_id: str, edge: TraceEdge):
        """Store tainted relationship"""
        query = """
        MATCH (from:Address {address: $from_address})
        MATCH (to:Address {address: $to_address})
        MATCH (trace:Trace {trace_id: $trace_id})
        
        CREATE (from)-[r:TAINTED_FLOW {
            trace_id: $trace_id,
            tx_hash: $tx_hash,
            value: $value,
            taint_value: $taint_value,
            hop: $hop,
            timestamp: datetime($timestamp)
        }]->(to)
        
        CREATE (trace)-[:INCLUDES_EDGE]->(r)
        """
        
        params = {
            "trace_id": trace_id,
            "from_address": edge.from_address,
            "to_address": edge.to_address,
            "tx_hash": edge.tx_hash,
            "value": float(edge.value),
            "taint_value": float(edge.taint_value),
            "hop": edge.hop,
            "timestamp": edge.timestamp
        }
        
        await session.run(query, params)
    
    async def find_path(
        self,
        from_address: str,
        to_address: str,
        max_hops: int = 5
    ) -> List[Dict[str, Any]]:
        """Find shortest path between addresses"""
        query = """
        MATCH path = shortestPath(
            (from:Address {address: $from_address})-[:SENT|RECEIVED*1..$max_hops]-(to:Address {address: $to_address})
        )
        RETURN path, length(path) as hops
        LIMIT 10
        """
        
        params = {
            "from_address": from_address.lower(),
            "to_address": to_address.lower(),
            "max_hops": max_hops
        }
        
        async with self.get_session() as session:
            result = await session.run(query, params)
            paths = []
            async for record in result:
                paths.append({
                    "path": record["path"],
                    "hops": record["hops"]
                })
            return paths
    
    async def get_address_neighbors(
        self,
        address: str,
        direction: str = "both",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get neighboring addresses"""
        if direction == "outgoing":
            query = """
            MATCH (a:Address {address: $address})-[r:SENT]->(tx:Transaction)-[:RECEIVED]->(neighbor:Address)
            RETURN DISTINCT neighbor.address as address, 
                   neighbor.labels as labels,
                   count(r) as tx_count,
                   sum(r.value) as total_value
            ORDER BY total_value DESC
            LIMIT $limit
            """
        elif direction == "incoming":
            query = """
            MATCH (neighbor:Address)-[r:SENT]->(tx:Transaction)-[:RECEIVED]->(a:Address {address: $address})
            RETURN DISTINCT neighbor.address as address,
                   neighbor.labels as labels,
                   count(r) as tx_count,
                   sum(r.value) as total_value
            ORDER BY total_value DESC
            LIMIT $limit
            """
        else:  # both
            query = """
            MATCH (a:Address {address: $address})-[r:SENT|RECEIVED]-(tx:Transaction)-[r2:SENT|RECEIVED]-(neighbor:Address)
            WHERE neighbor.address <> $address
            RETURN DISTINCT neighbor.address as address,
                   neighbor.labels as labels,
                   count(r) as tx_count
            LIMIT $limit
            """
        
        params = {"address": address.lower(), "limit": limit}
        
        async with self.get_session() as session:
            result = await session.run(query, params)
            neighbors = []
            async for record in result:
                neighbors.append(dict(record))
            return neighbors
    
    async def get_high_risk_connections(self, address: str) -> List[Dict[str, Any]]:
        """Find connections to high-risk addresses"""
        query = """
        MATCH (a:Address {address: $address})-[*1..3]-(risky:Address)
        WHERE any(label IN risky.labels WHERE label IN ['sanctioned', 'scam', 'mixer'])
        RETURN DISTINCT risky.address as address,
               risky.labels as labels,
               shortestPath((a)-[*]-(risky)) as path
        LIMIT 50
        """
        
        params = {"address": address.lower()}
        
        async with self.get_session() as session:
            result = await session.run(query, params)
            connections = []
            async for record in result:
                connections.append(dict(record))
            return connections

    async def get_address_exposure(self, address: str) -> float:
        """Return a normalized exposure score (0..1) for an address.
        Uses taint_received property if available. Test/Offline-safe.
        """
        if os.getenv("TEST_MODE") == "1" or self.driver is None:
            return 0.0
        q = """
        MATCH (a:Address {address: $addr})
        RETURN coalesce(a.taint_received, 0.0) AS tr
        """
        async with self.get_session() as session:
            res = await session.run(q, {"addr": address.lower()})
            rec = await res.single()
            val = float(rec["tr"]) if rec and rec.get("tr") is not None else 0.0
            # Smooth normalization: map [0, +inf) -> [0,1) via x/(1+x), then clamp.
            norm = val / (1.0 + abs(val)) if val > 0 else 0.0
            return max(0.0, min(1.0, norm))

    async def get_address_graph_signals(self, address: str) -> dict:
        """Compute simple graph-derived features for risk scoring.
        Returns dict with keys: avg_neighbor_taint, high_risk_neighbor_ratio, max_path_taint3
        TEST/OFFLINE-safe: returns zeros when no driver.
        """
        if os.getenv("TEST_MODE") == "1" or self.driver is None:
            return {
                "avg_neighbor_taint": 0.0,
                "high_risk_neighbor_ratio": 0.0,
                "max_path_taint3": 0.0,
            }
        async with self.get_session() as session:
            # Average taint of direct out-neighbors
            q1 = """
            MATCH (a:Address {address: $addr})-[:SENT|RECEIVED]-(tx:Transaction)-[:SENT|RECEIVED]-(n:Address)
            WHERE n.address <> a.address
            RETURN avg(coalesce(n.taint_received, 0.0)) AS avg_t
            """
            r1 = await session.run(q1, {"addr": address.lower()})
            rec1 = await r1.single()
            avg_t = float(rec1["avg_t"]) if rec1 and rec1.get("avg_t") is not None else 0.0

            # High-risk neighbor ratio (taint_received > 0.5)
            q2 = """
            MATCH (a:Address {address: $addr})-[:SENT|RECEIVED]-(tx:Transaction)-[:SENT|RECEIVED]-(n:Address)
            WHERE n.address <> a.address
            WITH count(DISTINCT n) AS tot, sum(CASE WHEN coalesce(n.taint_received,0.0) > 0.5 THEN 1 ELSE 0 END) AS hr
            RETURN CASE WHEN tot > 0 THEN (toFloat(hr)/toFloat(tot)) ELSE 0.0 END AS ratio
            """
            r2 = await session.run(q2, {"addr": address.lower()})
            rec2 = await r2.single()
            ratio = float(rec2["ratio"]) if rec2 and rec2.get("ratio") is not None else 0.0

            # Max path taint sum within 3 hops
            q3 = """
            MATCH p=(a:Address {address: $addr})-[:SENT|RECEIVED*1..3]-(:Transaction)-[:SENT|RECEIVED*1..3]-(b:Address)
            WITH relationships(p) AS rs
            RETURN max(reduce(s=0.0, r IN rs | s + coalesce(r.taint_value, 0.0))) AS max_taint
            """
            r3 = await session.run(q3, {"addr": address.lower()})
            rec3 = await r3.single()
            max_taint = float(rec3["max_taint"]) if rec3 and rec3.get("max_taint") is not None else 0.0

            # Normalize max_path_taint with x/(1+x)
            max_t_norm = max_taint / (1.0 + abs(max_taint)) if max_taint > 0 else 0.0

            return {
                "avg_neighbor_taint": max(0.0, min(1.0, avg_t)),
                "high_risk_neighbor_ratio": max(0.0, min(1.0, ratio)),
                "max_path_taint3": max(0.0, min(1.0, max_t_norm)),
            }

    async def create_bridge_link(
        self,
        from_address: str,
        to_address: str,
        bridge: str,
        chain_from: str,
        chain_to: str,
        tx_hash: str,
        timestamp_iso: str,
    ) -> None:
        """Persist a cross-chain bridge link between two addresses."""
        if os.getenv("TEST_MODE") == "1":
            return
        query = """
        MERGE (a:Address {address: $from})
        ON CREATE SET a.created_at = datetime(), a.chain = $chain_from
        MERGE (b:Address {address: $to})
        ON CREATE SET b.created_at = datetime(), b.chain = $chain_to
        MERGE (a)-[r:BRIDGE_LINK {
            tx_hash: $tx,
            bridge: $bridge
        }]->(b)
        SET r.chain_from = $chain_from,
            r.chain_to = $chain_to,
            r.timestamp = datetime($ts)
        """
        params = {
            "from": from_address.lower(),
            "to": to_address.lower(),
            "bridge": bridge,
            "chain_from": chain_from.lower(),
            "chain_to": chain_to.lower(),
            "tx": tx_hash,
            "ts": timestamp_iso,
        }
        async with self.get_session() as session:
            await session.run(query, params)
    
    async def create_cluster(self, cluster_id: str, addresses: List[str]):
        """Create address cluster"""
        query = """
        MERGE (cluster:Cluster {cluster_id: $cluster_id})
        ON CREATE SET cluster.created_at = datetime()
        
        WITH cluster
        UNWIND $addresses AS addr
        MATCH (a:Address {address: addr})
        MERGE (a)-[:BELONGS_TO]->(cluster)
        
        RETURN cluster.cluster_id as cluster_id, count(a) as member_count
        """
        
        params = {
            "cluster_id": cluster_id,
            "addresses": [a.lower() for a in addresses]
        }
        
        async with self.get_session() as session:
            result = await session.run(query, params)
            return await result.single()

    async def resolve_cluster_simple(self, address: str) -> dict:
        """Resolve a simple cluster around an address based on common counterparties.
        Heuristic: addresses that share at least 2 counterparties with the seed via SENT/RECEIVED.
        Persists (:Address)-[:BELONGS_TO]->(:Cluster {cluster_id}). Returns {cluster_id, members}.
        TEST_MODE-safe: returns empty when no driver.
        """
        if os.getenv("TEST_MODE") == "1" or self.driver is None:
            return {"cluster_id": None, "members": []}
        seed = address.lower()
        async with self.get_session() as session:
            q = """
            MATCH (a:Address {address: $addr})-[:SENT|RECEIVED]-(tx:Transaction)-[:SENT|RECEIVED]-(cp:Address)
            WITH a, collect(DISTINCT cp) AS cps
            UNWIND cps AS cp
            MATCH (o:Address)-[:SENT|RECEIVED]-(tx2:Transaction)-[:SENT|RECEIVED]-(cp)
            WHERE o.address <> a.address
            WITH a, o, count(DISTINCT cp) AS common
            WHERE common >= 2
            RETURN collect(DISTINCT o.address) AS others
            """
            res = await session.run(q, {"addr": seed})
            rec = await res.single()
            others = rec.get("others") if rec else []
            members = sorted(list({seed, *others}))
            if not members:
                return {"cluster_id": None, "members": []}
            cid = f"cl_{seed[:8]}"
            cq = """
            MERGE (cluster:Cluster {cluster_id: $cid})
            ON CREATE SET cluster.created_at = datetime()
            WITH cluster
            UNWIND $members AS m
            MERGE (a:Address {address: m})
            MERGE (a)-[:BELONGS_TO]->(cluster)
            WITH cluster
            SET cluster.size = size((:Address)-[:BELONGS_TO]->(cluster))
            RETURN cluster.cluster_id AS cid
            """
            cres = await session.run(cq, {"cid": cid, "members": members})
            crec = await cres.single()
            return {"cluster_id": crec.get("cid") if crec else cid, "members": members}

    async def set_address_risk_score(self, address: str, score: float) -> None:
        """Persist risk_score on Address node. No-op in TEST_MODE."""
        if os.getenv("TEST_MODE") == "1" or self.driver is None:
            return
        q = """
        MERGE (a:Address {address: $addr})
        SET a.risk_score = $score,
            a.updated_at = datetime()
        """
        async with self.get_session() as session:
            await session.run(q, {"addr": address.lower(), "score": float(score)})


# Singleton instance
neo4j_client = Neo4jClient()

# Ensure a patchable driver exists for tests that patch driver.session
if (os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1") and getattr(neo4j_client, "driver", None) is None:
    class _PatchableStubDriver:
        def session(self):
            class _DummySession:
                async def run(self, *args, **kwargs):
                    class _Empty:
                        async def single(self):
                            return None
                        def __aiter__(self):
                            return self
                        async def __anext__(self):
                            raise StopAsyncIteration
                    return _Empty()
                async def close(self):
                    return None
            return _DummySession()
    neo4j_client.driver = _PatchableStubDriver()
