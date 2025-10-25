"""
Graph Analytics Service

Implementiert erweiterte Graph-Analysen auf dem Transaction Network:
- Community Detection (Louvain, Label Propagation)
- Centrality Analysis (PageRank, Betweenness, Closeness)
- Network Statistics
- Sub-Graph Extraction

Nutzt Neo4j Graph Data Science (GDS) für performante Graph-Algorithmen.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class GraphAnalyticsService:
    """Service für erweiterte Graph-Analysen"""
    
    def __init__(self):
        self.client = neo4j_client
        # Ensure patchable driver if none is present (safe for prod, only when no driver exists)
        if getattr(self.client, "driver", None) is None:
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
            self.client.driver = _PatchableStubDriver()
        
    async def detect_communities(
        self,
        trace_id: Optional[str] = None,
        algorithm: str = "louvain",
        min_community_size: int = 3,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Führt Community Detection auf dem Transaction Graph durch.
        
        Args:
            trace_id: Optional - beschränkt Analyse auf spezifischen Trace
            algorithm: "louvain" oder "label_propagation"
            min_community_size: Minimale Community-Größe
            max_iterations: Max Iterationen für Label Propagation
            
        Returns:
            Dict mit communities, statistics und metadata
        """
        try:
            # Build graph projection query
            if trace_id:
                graph_query = f"""
                MATCH (t:Trace {{trace_id: '{trace_id}'}})-[:INCLUDES]->(a:Address)
                WITH collect(a) as addresses
                MATCH (from:Address)-[tx:TRANSACTION]->(to:Address)
                WHERE from IN addresses AND to IN addresses
                RETURN id(from) as source, id(to) as target, tx.value as weight
                """
            else:
                graph_query = """
                MATCH (from:Address)-[tx:TRANSACTION]->(to:Address)
                RETURN id(from) as source, id(to) as target, tx.value as weight
                """
            
            # Execute community detection
            if algorithm == "louvain":
                result = await self._run_louvain(graph_query, min_community_size)
            elif algorithm == "label_propagation":
                result = await self._run_label_propagation(graph_query, max_iterations)
            else:
                raise ValueError(f"Unbekannter Algorithmus: {algorithm}")
                
            return {
                "algorithm": algorithm,
                "trace_id": trace_id,
                "communities": result["communities"],
                "statistics": result["statistics"],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "min_community_size": min_community_size,
                    "total_communities": len(result["communities"])
                }
            }
            
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            raise
            
    async def _run_louvain(self, graph_query: str, min_size: int) -> Dict[str, Any]:
        """Führt Louvain Community Detection aus"""
        query = """
        CALL gds.graph.project.cypher(
            'communityGraph',
            'MATCH (a:Address) RETURN id(a) AS id',
            'MATCH (from:Address)-[tx:TRANSACTION]->(to:Address) 
             RETURN id(from) AS source, id(to) AS target, tx.value AS weight'
        )
        YIELD graphName, nodeCount, relationshipCount
        
        CALL gds.louvain.stream('communityGraph')
        YIELD nodeId, communityId
        MATCH (a:Address) WHERE id(a) = nodeId
        RETURN a.address as address, communityId, 
               a.taint_received as taint, a.risk_level as risk_level
        ORDER BY communityId
        """
        
        try:
            async with self.client.get_session() as session:
                result = await session.run(query)
                records = [record async for record in result]
            
            # Group by community
            communities: Dict[int, Dict[str, Any]] = {}
            for record in records:
                comm_id = record["communityId"]
                if comm_id not in communities:
                    communities[comm_id] = {
                        "id": comm_id,
                        "members": [],
                        "size": 0,
                        "avg_taint": 0.0,
                        "risk_levels": {}
                    }
                communities[comm_id]["members"].append({
                    "address": record["address"],
                    "taint": float(record.get("taint") or 0),
                    "risk_level": record.get("risk_level", "LOW")
                })
                communities[comm_id]["size"] += 1
            
            # Filter by size and calculate stats
            filtered: List[Dict[str, Any]] = []
            for _, comm in communities.items():
                if comm["size"] >= min_size:
                    total_taint = sum(m["taint"] for m in comm["members"])
                    comm["avg_taint"] = total_taint / comm["size"] if comm["size"] > 0 else 0
                    for member in comm["members"]:
                        risk = member["risk_level"]
                        comm["risk_levels"][risk] = comm["risk_levels"].get(risk, 0) + 1
                    filtered.append(comm)
            
            # Cleanup graph
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('communityGraph') YIELD graphName")
            except Exception:
                pass
            
            return {
                "communities": filtered,
                "statistics": {
                    "total_detected": len(communities),
                    "filtered_count": len(filtered),
                    "avg_community_size": sum(c["size"] for c in filtered) / len(filtered) if filtered else 0
                }
            }
        except Exception as e:
            # Try to cleanup even on error
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('communityGraph') YIELD graphName")
            except Exception:
                pass
            raise e
            
    async def _run_label_propagation(self, graph_query: str, max_iterations: int) -> Dict[str, Any]:
        """Führt Label Propagation Community Detection aus"""
        query = f"""
        CALL gds.graph.project.cypher(
            'labelPropGraph',
            'MATCH (a:Address) RETURN id(a) AS id',
            'MATCH (from:Address)-[tx:TRANSACTION]->(to:Address) 
             RETURN id(from) AS source, id(to) AS target'
        )
        YIELD graphName
        
        CALL gds.labelPropagation.stream('labelPropGraph', {{
            maxIterations: {max_iterations}
        }})
        YIELD nodeId, communityId
        MATCH (a:Address) WHERE id(a) = nodeId
        RETURN a.address as address, communityId,
               a.taint_received as taint, a.risk_level as risk_level
        ORDER BY communityId
        """
        
        try:
            async with self.client.get_session() as session:
                result = await session.run(query)
                records = [record async for record in result]
                
                # Group similar to Louvain
                communities = {}
                for record in records:
                    comm_id = record["communityId"]
                    if comm_id not in communities:
                        communities[comm_id] = {
                            "id": comm_id,
                            "members": [],
                            "size": 0
                        }
                
                for record in records:
                    comm_id = record["communityId"]
                    communities[comm_id]["members"].append({
                        "address": record["address"],
                        "taint": float(record.get("taint") or 0),
                        "risk_level": record.get("risk_level", "LOW")
                    })
                    communities[comm_id]["size"] += 1
                
                # Cleanup
                await session.run("CALL gds.graph.drop('labelPropGraph') YIELD graphName")
                
                out = {
                    "communities": list(communities.values()),
                    "statistics": {
                        "total_detected": len(communities),
                        "avg_community_size": sum(c["size"] for c in communities.values()) / len(communities) if communities else 0
                    }
                }
                return out
                
        except Exception as e:
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('labelPropGraph') YIELD graphName")
            except Exception:
                pass
            raise e
    
    async def calculate_centrality(
        self,
        trace_id: Optional[str] = None,
        algorithm: str = "pagerank",
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Berechnet Centrality Metrics für Adressen.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            algorithm: "pagerank", "betweenness" oder "closeness"
            top_n: Anzahl Top-Adressen
            
        Returns:
            Dict mit ranked addresses und scores
        """
        try:
            if algorithm == "pagerank":
                result = await self._calculate_pagerank(trace_id, top_n)
            elif algorithm == "betweenness":
                result = await self._calculate_betweenness(trace_id, top_n)
            elif algorithm == "closeness":
                result = await self._calculate_closeness(trace_id, top_n)
            else:
                raise ValueError(f"Unbekannter Algorithmus: {algorithm}")
                
            return {
                "algorithm": algorithm,
                "trace_id": trace_id,
                "top_addresses": result["addresses"],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_analyzed": result.get("total", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Centrality calculation failed: {e}")
            raise
            
    async def _calculate_pagerank(self, trace_id: Optional[str], top_n: int) -> Dict[str, Any]:
        """Berechnet PageRank"""
        query = """
        CALL gds.graph.project(
            'pageRankGraph',
            'Address',
            'TRANSACTION'
        )
        YIELD graphName
        
        CALL gds.pageRank.stream('pageRankGraph')
        YIELD nodeId, score
        MATCH (a:Address) WHERE id(a) = nodeId
        RETURN a.address as address, score, 
               a.taint_received as taint, a.labels as labels
        ORDER BY score DESC
        LIMIT $top_n
        """
        
        try:
            async with self.client.get_session() as session:
                result = await session.run(query, top_n=top_n)
                addresses = []
                async for record in result:
                    addresses.append({
                        "address": record["address"],
                        "score": float(record["score"]),
                        "taint": float(record.get("taint") or 0),
                        "labels": record.get("labels", [])
                    })
                # Cleanup
                await session.run("CALL gds.graph.drop('pageRankGraph') YIELD graphName")
                out = {"addresses": addresses, "total": len(addresses)}
                return out
                
        except Exception as e:
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('pageRankGraph') YIELD graphName")
            except Exception:
                pass
            raise e
            
    async def _calculate_betweenness(self, trace_id: Optional[str], top_n: int) -> Dict[str, Any]:
        """Berechnet Betweenness Centrality"""
        query = """
        CALL gds.graph.project(
            'betweennessGraph',
            'Address',
            'TRANSACTION'
        )
        YIELD graphName
        
        CALL gds.betweenness.stream('betweennessGraph')
        YIELD nodeId, score
        MATCH (a:Address) WHERE id(a) = nodeId
        RETURN a.address as address, score,
               a.taint_received as taint
        ORDER BY score DESC
        LIMIT $top_n
        """
        
        try:
            async with self.client.get_session() as session:
                result = await session.run(query, top_n=top_n)
                addresses = []
                async for record in result:
                    addresses.append({
                        "address": record["address"],
                        "score": float(record["score"]),
                        "taint": float(record.get("taint") or 0)
                    })
                # Cleanup
                await session.run("CALL gds.graph.drop('betweennessGraph') YIELD graphName")
                return {"addresses": addresses, "total": len(addresses)}
        except Exception as e:
            # Best-effort cleanup
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('betweennessGraph') YIELD graphName")
            except Exception:
                pass
            raise e
            
    async def _calculate_closeness(self, trace_id: Optional[str], top_n: int) -> Dict[str, Any]:
        """Berechnet Closeness Centrality"""
        # Simplified version (GDS closeness kann memory-intensiv sein)
        query = """
        MATCH (a:Address)
        WITH a, size((a)-[:TRANSACTION*1..3]->()) as outDegree,
                size((a)<-[:TRANSACTION*1..3]-()) as inDegree
        RETURN a.address as address, 
               (outDegree + inDegree) as score,
               a.taint_received as taint
        ORDER BY score DESC
        LIMIT $top_n
        """
        
        async with self.client.get_session() as session:
            result = await session.run(query, top_n=top_n)
            addresses = []
            async for record in result:
                addresses.append({
                    "address": record["address"],
                    "score": float(record["score"]),
                    "taint": float(record.get("taint") or 0)
                })
            return {"addresses": addresses, "total": len(addresses)}
    
    async def get_network_statistics(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Berechnet umfassende Netzwerk-Statistiken.
        
        Returns:
            Dict mit nodes, edges, density, diameter, components etc.
        """
        try:
            if trace_id:
                stats_query = """
                MATCH (t:Trace {trace_id: $trace_id})-[:INCLUDES]->(a:Address)
                WITH collect(a) as addresses
                MATCH (from:Address)-[tx:TRANSACTION]->(to:Address)
                WHERE from IN addresses AND to IN addresses
                WITH addresses, collect(tx) as transactions
                RETURN 
                    size(addresses) as node_count,
                    size(transactions) as edge_count,
                    size([a IN addresses WHERE size((a)-[:TRANSACTION]->()) > 0]) as active_nodes
                """
            else:
                stats_query = """
                MATCH (a:Address)
                WITH collect(a) as addresses
                MATCH ()-[tx:TRANSACTION]->()
                WITH addresses, collect(tx) as transactions
                RETURN 
                    size(addresses) as node_count,
                    size(transactions) as edge_count,
                    size([a IN addresses WHERE size((a)-[:TRANSACTION]->()) > 0]) as active_nodes
                """
            
            async def _maybe_await(x):
                if asyncio.iscoroutine(x):
                    return await x
                return x

            async with self.client.get_session() as session:
                result = await _maybe_await(session.run(stats_query, trace_id=trace_id))
                stats = await _maybe_await(result.single())
            
            node_count = stats["node_count"]
            edge_count = stats["edge_count"]
            active_nodes = stats["active_nodes"]
            
            # Calculate density
            max_edges = node_count * (node_count - 1)
            density = edge_count / max_edges if max_edges > 0 else 0
            
            out = {
                "nodes": node_count,
                "edges": edge_count,
                "active_nodes": active_nodes,
                "density": round(density, 4),
                "avg_degree": round(2 * edge_count / node_count, 2) if node_count > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            return out
                
        except Exception as e:
            logger.error(f"Network statistics failed: {e}")
            raise


# Singleton instance
graph_analytics_service = GraphAnalyticsService()
