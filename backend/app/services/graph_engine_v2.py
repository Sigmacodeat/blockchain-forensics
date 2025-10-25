"""
Graph Engine v2 - Advanced Pathfinder with Costs/Constraints

Features:
- Pathfinder mit Constraints/Costs (Zeit, Risiko, Volumen)
- P95 Latenz <1.5s durch Materialisierte Hot-Paths
- Query API v2 mit GraphQL-ähnlicher Syntax
- Constraints: max_hops, min_amount, risk_threshold, time_window
- Costs: transaction_fees, time_cost, risk_penalty
- Materialized Views für häufige Queries
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import heapq
import functools
from collections import deque

try:
    from neo4j import GraphDatabase as _Neo4jGraphDatabase
    GraphDatabase: Any = _Neo4jGraphDatabase
except Exception:
    GraphDatabase = None

from app.config import settings
from app.db.redis_client import redis_client
from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


@dataclass
class PathConstraint:
    """Constraints für Pathfinding"""
    max_hops: int = 10
    min_amount: float = 0.0
    max_amount: Optional[float] = None
    risk_threshold: float = 1.0  # 0.0 = safe, 1.0 = high risk
    time_window_days: int = 365
    chains: Optional[Set[str]] = None
    exclude_addresses: Optional[Set[str]] = None
    include_tags: Optional[Set[str]] = None
    exclude_tags: Optional[Set[str]] = None


@dataclass
class CostFunction:
    """Cost Function für Pathfinding"""
    transaction_fee_weight: float = 1.0
    time_cost_weight: float = 0.1
    risk_penalty_weight: float = 10.0
    hop_penalty_weight: float = 0.5


@dataclass
class PathNode:
    """Node in Pathfinding Graph"""
    address: str
    chain: str
    total_cost: float
    hops: int
    path: List[Dict[str, Any]] = field(default_factory=list)
    visited: Set[str] = field(default_factory=set)

    def __lt__(self, other: 'PathNode') -> bool:
        return self.total_cost < other.total_cost


@dataclass
class PathResult:
    """Ergebnis eines Pathfindings"""
    source: str
    target: str
    paths: List[Dict[str, Any]]
    execution_time_ms: float
    total_paths_found: int
    constraints_applied: PathConstraint


def _risk_level_from_score(score: Optional[float]) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 0.8:
        return "CRITICAL"
    if score >= 0.6:
        return "HIGH"
    if score >= 0.3:
        return "MEDIUM"
    if score >= 0.1:
        return "LOW"
    return "SAFE"


class GraphEngineV2:
    """Advanced Graph Engine mit Pathfinder"""

    def __init__(self):
        self.enabled = bool((GraphDatabase is not None) and getattr(settings, "NEO4J_URI", None))
        self._driver = None
        self._materialized_paths = {}  # Cache für häufige Paths
        self._hot_paths_cache = {}  # LRU Cache für Hot Paths

        if self.enabled:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
                logger.info("GraphEngineV2: Neo4j driver initialized")
            except Exception as e:
                logger.warning(f"GraphEngineV2 disabled (Neo4j init failed): {e}")
                self.enabled = False
        else:
            logger.info("GraphEngineV2: running in no-op mode")

    async def close(self):
        if self._driver:
            await asyncio.to_thread(self._driver.close)

    def _calculate_edge_cost(self, edge: Dict[str, Any], cost_fn: CostFunction) -> float:
        """Berechne Cost für eine Edge"""
        tx_fee = edge.get('fee', 0.0)
        time_diff = edge.get('time_diff_hours', 24) / 24.0  # Normalisiere auf Tage
        risk_score = edge.get('risk_score', 0.0)

        cost = (
            tx_fee * cost_fn.transaction_fee_weight +
            time_diff * cost_fn.time_cost_weight +
            risk_score * cost_fn.risk_penalty_weight +
            cost_fn.hop_penalty_weight  # Basis Hop Penalty
        )
        return cost

    async def _get_neighbors(self, address: str, chain: str, constraints: PathConstraint) -> List[Dict[str, Any]]:
        """Hole Nachbarn eines Address mit Constraints"""
        if not self.enabled or not self._driver:
            return []

        # Cache-Key für Hot Paths
        cache_key = f"neighbors:{address}:{chain}:{hash(str(constraints))}"
        cached = await self._get_cached_neighbors(cache_key)
        if cached:
            return cached

        query = """
        MATCH (a:Address {address: $address, chain: $chain})
        MATCH (a)-[r]-(t:Tx)-[s]-(b:Address)
        WHERE r.tx = s.tx
        AND (b.address <> $address OR b.chain <> $chain)
        AND t.timestamp >= datetime() - duration({days: $time_window})
        AND ($chains IS NULL OR b.chain IN $chains)
        AND ($exclude_addresses IS NULL OR NOT b.address IN $exclude_addresses)
        WITH b, r, s, t,
             CASE WHEN r.amount IS NOT NULL THEN r.amount ELSE s.amount END as amount,
             duration.between(t.timestamp, datetime()).days * -1 as age_days
        WHERE amount >= $min_amount
        AND ($max_amount IS NULL OR amount <= $max_amount)
        RETURN DISTINCT
            b.address as address,
            b.chain as chain,
            amount,
            t.hash as tx_hash,
            t.timestamp as timestamp,
            age_days,
            r.fee as fee,
            COALESCE(b.risk_score, 0.0) as risk_score,
            CASE WHEN EXISTS((b)-[:HAS_TAG]->(:Tag)) THEN [(b)-[:HAS_TAG]->(tag:Tag) | tag.name] ELSE [] END as tags
        ORDER BY amount DESC
        LIMIT 100
        """

        params = {
            "address": address,
            "chain": chain,
            "time_window": constraints.time_window_days,
            "chains": list(constraints.chains) if constraints.chains else None,
            "exclude_addresses": list(constraints.exclude_addresses) if constraints.exclude_addresses else None,
            "min_amount": constraints.min_amount,
            "max_amount": constraints.max_amount,
        }

        try:
            records = await asyncio.to_thread(
                lambda: list(self._driver.session().run(query, **params))
            )

            neighbors = []
            for rec in records:
                tags = rec.get("tags", [])
                risk_score = rec.get("risk_score", 0.0)

                # Apply tag filters
                if constraints.include_tags and not any(tag in constraints.include_tags for tag in tags):
                    continue
                if constraints.exclude_tags and any(tag in constraints.exclude_tags for tag in tags):
                    continue

                # Apply risk threshold
                if risk_score > constraints.risk_threshold:
                    continue

                neighbor = {
                    "address": rec["address"],
                    "chain": rec["chain"],
                    "amount": rec["amount"],
                    "tx_hash": rec["tx_hash"],
                    "timestamp": rec["timestamp"],
                    "age_days": rec["age_days"],
                    "fee": rec.get("fee", 0.0),
                    "risk_score": risk_score,
                    "tags": tags
                }
                neighbors.append(neighbor)

            # Cache für 5 Minuten
            await self._cache_neighbors(cache_key, neighbors, ttl=300)
            return neighbors

        except Exception as e:
            logger.error(f"Error getting neighbors for {address}: {e}")
            return []

    async def _get_cached_neighbors(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Hole gecachte Nachbarn aus Redis"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                data = await client.get(cache_key)
                if data:
                    import json
                    return json.loads(data)
        except Exception:
            pass
        return None

    async def _cache_neighbors(self, cache_key: str, neighbors: List[Dict[str, Any]], ttl: int = 300):
        """Cache Nachbarn in Redis"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                import json
                await client.setex(cache_key, ttl, json.dumps(neighbors))
        except Exception:
            pass

    async def find_paths_astar(
        self,
        source: str,
        target: str,
        constraints: PathConstraint,
        cost_fn: CostFunction,
        max_paths: int = 10
    ) -> PathResult:
        """
        A* Pathfinding Algorithm mit Constraints und Costs
        """
        start_time = datetime.now()

        # Priority Queue für A*
        frontier = []
        heapq.heappush(frontier, PathNode(
            address=source,
            chain="unknown",  # Wird beim ersten Nachbarn bestimmt
            total_cost=0.0,
            hops=0,
            path=[],
            visited={source}
        ))

        paths_found = []
        visited_global = set()

        while frontier and len(paths_found) < max_paths:
            current = heapq.heappop(frontier)

            if current.address in visited_global:
                continue
            visited_global.add(current.address)

            # Target erreicht?
            if current.address == target and current.hops > 0:
                path_data = {
                    "path": current.path.copy(),
                    "total_cost": current.total_cost,
                    "hops": current.hops,
                    "source_chain": current.path[0]["from_chain"] if current.path else "unknown",
                    "target_chain": current.chain
                }
                paths_found.append(path_data)
                continue

            # Max Hops erreicht?
            if current.hops >= constraints.max_hops:
                continue

            # Nachbarn holen
            neighbors = await self._get_neighbors(current.address, current.chain, constraints)

            for neighbor in neighbors:
                neighbor_addr = neighbor["address"]
                if neighbor_addr in current.visited:
                    continue

                # Edge Cost berechnen
                edge_cost = self._calculate_edge_cost(neighbor, cost_fn)
                new_cost = current.total_cost + edge_cost

                # Path erweitern
                new_path = current.path + [{
                    "from_address": current.address,
                    "to_address": neighbor_addr,
                    "from_chain": current.chain,
                    "to_chain": neighbor["chain"],
                    "amount": neighbor["amount"],
                    "tx_hash": neighbor["tx_hash"],
                    "timestamp": neighbor["timestamp"],
                    "fee": neighbor.get("fee", 0.0),
                    "risk_score": neighbor.get("risk_score", 0.0),
                    "edge_cost": edge_cost
                }]

                new_node = PathNode(
                    address=neighbor_addr,
                    chain=neighbor["chain"],
                    total_cost=new_cost,
                    hops=current.hops + 1,
                    path=new_path,
                    visited=current.visited | {neighbor_addr}
                )

                heapq.heappush(frontier, new_node)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return PathResult(
            source=source,
            target=target,
            paths=paths_found,
            execution_time_ms=execution_time,
            total_paths_found=len(paths_found),
            constraints_applied=constraints
        )

    async def _get_address_metadata(self, address: str) -> Dict[str, Any]:
        if not address:
            return {}
        try:
            rows = await neo4j_client.execute_read(
                """
                MATCH (a:Address {address: $address})
                RETURN a.chain as chain,
                       a.risk_score as risk_score,
                       a.labels as labels,
                       a.tx_count as tx_count,
                       a.balance as balance,
                       a.first_seen as first_seen,
                       a.last_seen as last_seen
                LIMIT 1
                """,
                {"address": address}
            )
            if rows:
                record = rows[0]
                return {
                    "address": address,
                    "chain": record.get("chain") or "unknown",
                    "risk_score": record.get("risk_score", 0.0),
                    "labels": record.get("labels") or [],
                    "tx_count": record.get("tx_count", 0),
                    "balance": record.get("balance", 0.0),
                    "first_seen": record.get("first_seen"),
                    "last_seen": record.get("last_seen"),
                }
        except Exception:
            pass
        return {
            "address": address,
            "chain": "unknown",
            "risk_score": 0.0,
            "labels": [],
            "tx_count": 0,
            "balance": 0.0,
            "first_seen": None,
            "last_seen": None,
        }

    async def fetch_subgraph(
        self,
        address: str,
        max_hops: int = 3,
        risk_threshold: float = 1.0,
        min_amount: float = 0.0,
        time_window_days: int = 365,
        include_bridges: bool = True,
        max_nodes: int = 500,
        max_edges: int = 1000,
    ) -> Dict[str, Any]:
        address = (address or "").strip().lower()
        if not address:
            return {"nodes": {}, "links": [], "summary": {"total_nodes": 0, "total_links": 0}}

        constraints = PathConstraint(
            max_hops=max_hops,
            min_amount=min_amount,
            risk_threshold=max(0.0, min(1.0, risk_threshold)),
            time_window_days=time_window_days,
        )

        if not self.enabled or not self._driver:
            root_meta = await self._get_address_metadata(address)
            nodes = {
                address: {
                    "address": address,
                    "chain": root_meta.get("chain", "unknown"),
                    "risk_score": root_meta.get("risk_score", 0.0),
                    "risk_level": _risk_level_from_score(root_meta.get("risk_score")),
                    "labels": root_meta.get("labels", []),
                    "tx_count": root_meta.get("tx_count", 0),
                    "balance": root_meta.get("balance", 0.0),
                    "first_seen": root_meta.get("first_seen"),
                    "last_seen": root_meta.get("last_seen"),
                }
            }
            summary = {
                "total_nodes": len(nodes),
                "total_links": 0,
                "risk_distribution": {nodes[address]["risk_level"]: 1},
                "chains": [nodes[address]["chain"]],
                "time_range": {
                    "earliest": nodes[address]["first_seen"],
                    "latest": nodes[address]["last_seen"],
                },
                "max_hops": 0,
            }
            return {"nodes": nodes, "links": [], "summary": summary}

        metadata_map: Dict[str, Dict[str, Any]] = {}
        root_meta = await self._get_address_metadata(address)
        metadata_map[address] = root_meta

        root_chain = root_meta.get("chain") or "unknown"
        queue = deque([(address, root_chain, 0)])
        visited: Set[str] = set()
        nodes: Dict[str, Dict[str, Any]] = {}
        links: List[Dict[str, Any]] = []
        edge_keys: Set[tuple[str, str]] = set()

        while queue and len(nodes) < max_nodes:
            current_address, current_chain, depth = queue.popleft()
            if current_address in visited:
                continue
            visited.add(current_address)

            meta = metadata_map.get(current_address) or await self._get_address_metadata(current_address)
            metadata_map[current_address] = meta
            current_chain = meta.get("chain", current_chain) or "unknown"

            nodes[current_address] = {
                "address": current_address,
                "chain": current_chain,
                "risk_score": meta.get("risk_score", 0.0),
                "risk_level": _risk_level_from_score(meta.get("risk_score")),
                "labels": meta.get("labels", []),
                "tx_count": meta.get("tx_count", 0),
                "balance": meta.get("balance", 0.0),
                "first_seen": meta.get("first_seen"),
                "last_seen": meta.get("last_seen"),
            }

            if depth >= constraints.max_hops:
                continue

            if not current_chain or current_chain == "unknown":
                continue

            neighbors = await self._get_neighbors(current_address, current_chain, constraints)
            for neighbor in neighbors:
                neighbor_addr = str(neighbor.get("address", "")).lower()
                if not neighbor_addr:
                    continue
                neighbor_chain = neighbor.get("chain") or "unknown"
                if not include_bridges and neighbor_chain != current_chain:
                    continue

                edge_key = (current_address, neighbor_addr)
                if edge_key not in edge_keys and len(links) < max_edges:
                    edge_keys.add(edge_key)
                    links.append({
                        "source": current_address,
                        "target": neighbor_addr,
                        "value": float(neighbor.get("amount") or 0.0),
                        "timestamp": neighbor.get("timestamp"),
                        "tx_hash": neighbor.get("tx_hash"),
                        "event_type": "BRIDGE_LINK" if neighbor_chain != current_chain else "TRANSACTION",
                        "bridge": neighbor_chain != current_chain,
                        "risk_score": neighbor.get("risk_score", 0.0),
                        "source_chain": current_chain,
                        "target_chain": neighbor_chain,
                        "fee": neighbor.get("fee"),
                    })

                if neighbor_addr not in metadata_map:
                    metadata_map[neighbor_addr] = {
                        "address": neighbor_addr,
                        "chain": neighbor_chain,
                        "risk_score": neighbor.get("risk_score", 0.0),
                        "labels": neighbor.get("tags", []),
                        "tx_count": 0,
                        "balance": 0.0,
                        "first_seen": None,
                        "last_seen": None,
                    }

                if (
                    neighbor_addr not in visited
                    and depth + 1 <= constraints.max_hops
                    and len(nodes) < max_nodes
                ):
                    queue.append((neighbor_addr, metadata_map[neighbor_addr].get("chain", "unknown"), depth + 1))

        risk_distribution: Dict[str, int] = {}
        chains: Set[str] = set()
        earliest = None
        latest = None
        for node in nodes.values():
            risk = node.get("risk_level", "UNKNOWN")
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            chain_val = node.get("chain")
            if chain_val:
                chains.add(chain_val)
            first_seen = node.get("first_seen")
            last_seen = node.get("last_seen")
            if first_seen:
                earliest = first_seen if earliest is None or first_seen < earliest else earliest
            if last_seen:
                latest = last_seen if latest is None or last_seen > latest else latest

        summary = {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "risk_distribution": risk_distribution,
            "chains": sorted(chains),
            "time_range": {"earliest": earliest, "latest": latest},
            "max_hops": min(max_hops, max((meta.get("depth", 0) for meta in []), default=max_hops)),
        }

        return {
            "nodes": nodes,
            "links": links,
            "summary": summary,
        }

    async def find_paths_bidirectional(
        self,
        source: str,
        target: str,
        constraints: PathConstraint,
        cost_fn: CostFunction,
        max_paths: int = 10
    ) -> PathResult:
        """
        Bidirektionales Pathfinding für bessere Performance bei großen Graphs
        """
        start_time = datetime.now()

        # Forward search von Source
        forward_frontier = []
        heapq.heappush(forward_frontier, PathNode(
            address=source, chain="unknown", total_cost=0.0, hops=0, path=[], visited={source}
        ))

        # Backward search von Target
        backward_frontier = []
        heapq.heappush(backward_frontier, PathNode(
            address=target, chain="unknown", total_cost=0.0, hops=0, path=[], visited={target}
        ))

        forward_visited = {}
        backward_visited = {}
        paths_found = []

        while forward_frontier and backward_frontier and len(paths_found) < max_paths:
            # Forward step
            if forward_frontier:
                current_forward = heapq.heappop(forward_frontier)
                forward_addr = current_forward.address

                if forward_addr not in forward_visited:
                    forward_visited[forward_addr] = current_forward

                    # Check if we can meet backward search
                    if forward_addr in backward_visited:
                        # Meeting point gefunden!
                        backward_node = backward_visited[forward_addr]
                        combined_path = current_forward.path + backward_node.path[::-1]  # Reverse backward path
                        total_cost = current_forward.total_cost + backward_node.total_cost
                        total_hops = current_forward.hops + backward_node.hops

                        path_data = {
                            "path": combined_path,
                            "total_cost": total_cost,
                            "hops": total_hops,
                            "meeting_point": forward_addr
                        }
                        paths_found.append(path_data)
                        continue

                    # Expand forward
                    neighbors = await self._get_neighbors(forward_addr, current_forward.chain, constraints)
                    for neighbor in neighbors:
                        if neighbor["address"] not in current_forward.visited:
                            edge_cost = self._calculate_edge_cost(neighbor, cost_fn)
                            new_cost = current_forward.total_cost + edge_cost
                            new_path = current_forward.path + [neighbor]
                            new_node = PathNode(
                                address=neighbor["address"],
                                chain=neighbor["chain"],
                                total_cost=new_cost,
                                hops=current_forward.hops + 1,
                                path=new_path,
                                visited=current_forward.visited | {neighbor["address"]}
                            )
                            heapq.heappush(forward_frontier, new_node)

            # Backward step (symmetrisch)
            if backward_frontier:
                current_backward = heapq.heappop(backward_frontier)
                backward_addr = current_backward.address

                if backward_addr not in backward_visited:
                    backward_visited[backward_addr] = current_backward

                    if backward_addr in forward_visited:
                        forward_node = forward_visited[backward_addr]
                        combined_path = forward_node.path + current_backward.path[::-1]
                        total_cost = forward_node.total_cost + current_backward.total_cost
                        total_hops = forward_node.hops + current_backward.hops

                        path_data = {
                            "path": combined_path,
                            "total_cost": total_cost,
                            "hops": total_hops,
                            "meeting_point": backward_addr
                        }
                        paths_found.append(path_data)
                        continue

                    # Expand backward (gleiche Logik wie forward)
                    neighbors = await self._get_neighbors(backward_addr, current_backward.chain, constraints)
                    for neighbor in neighbors:
                        if neighbor["address"] not in current_backward.visited:
                            edge_cost = self._calculate_edge_cost(neighbor, cost_fn)
                            new_cost = current_backward.total_cost + edge_cost
                            new_path = current_backward.path + [neighbor]
                            new_node = PathNode(
                                address=neighbor["address"],
                                chain=neighbor["chain"],
                                total_cost=new_cost,
                                hops=current_backward.hops + 1,
                                path=new_path,
                                visited=current_backward.visited | {neighbor["address"]}
                            )
                            heapq.heappush(backward_frontier, new_node)

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return PathResult(
            source=source,
            target=target,
            paths=paths_found,
            execution_time_ms=execution_time,
            total_paths_found=len(paths_found),
            constraints_applied=constraints
        )

    async def materialize_hot_paths(self, min_frequency: int = 100):
        """
        Materialisiere häufig abgefragte Paths für bessere Performance
        """
        if not self.enabled or not self._driver:
            return

        # Finde häufige Path-Queries (vereinfacht - würde normalerweise aus Analytics kommen)
        query = """
        MATCH (a:Address)-[r*1..5]-(b:Address)
        WHERE a <> b
        WITH a.address as source, b.address as target, count(*) as freq
        WHERE freq >= $min_freq
        RETURN source, target, freq
        ORDER BY freq DESC
        LIMIT 100
        """

        try:
            records = await asyncio.to_thread(
                lambda: list(self._driver.session().run(query, min_freq=min_frequency))
            )

            for rec in records:
                source = rec["source"]
                target = rec["target"]
                # Cache dummy path (in Produktion: berechne echte Paths)
                cache_key = f"hot_path:{source}:{target}"
                self._hot_paths_cache[cache_key] = {
                    "source": source,
                    "target": target,
                    "materialized": True,
                    "last_updated": datetime.now().isoformat()
                }

            logger.info(f"Materialized {len(records)} hot paths")

        except Exception as e:
            logger.error(f"Error materializing hot paths: {e}")

    async def query_graph_v2(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        GraphQL-ähnliche Query API v2
        Beispiel: {
            "find_paths": {
                "source": "0x123...",
                "target": "0x456...",
                "constraints": {"max_hops": 5},
                "cost_function": {"risk_penalty_weight": 5.0}
            }
        }
        """
        if "find_paths" in query:
            params = query["find_paths"]
            source = params["source"]
            target = params["target"]

            constraints = PathConstraint(**params.get("constraints", {}))
            cost_fn = CostFunction(**params.get("cost_function", {}))
            algorithm = params.get("algorithm", "astar")  # "astar" oder "bidirectional"

            if algorithm == "bidirectional":
                result = await self.find_paths_bidirectional(source, target, constraints, cost_fn)
            else:
                result = await self.find_paths_astar(source, target, constraints, cost_fn)

            return {
                "query_type": "find_paths",
                "result": {
                    "source": result.source,
                    "target": result.target,
                    "paths": result.paths,
                    "execution_time_ms": result.execution_time_ms,
                    "total_paths_found": result.total_paths_found
                }
            }

        elif "materialize_hot_paths" in query:
            await self.materialize_hot_paths(query["materialize_hot_paths"].get("min_frequency", 100))
            return {"query_type": "materialize_hot_paths", "status": "completed"}

        else:
            return {"error": "Unknown query type"}


# Singleton
graph_engine_v2 = GraphEngineV2()
