"""
Advanced Graph Analytics - Louvain Community Detection
======================================================

Implementiert erweiterte Graph-Analysen für Wallet-Clustering:
- Louvain-Community-Detection für optimale Cluster-Erkennung
- Zentralitätsmaße (Degree, Betweenness, Closeness)
- Graph-Metrik-Berechnung
- Integration mit Neo4j für große Graphen
"""

from __future__ import annotations
import logging
from typing import Dict, List, Any, Optional
import networkx as nx
from datetime import datetime

# Import Neo4j client for graph queries
try:
    from app.db.neo4j_client import neo4j_client
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

# Import metrics for graph analytics
try:
    from app.observability.metrics import (
        GRAPH_ANALYTICS_COMPUTATION_TIME,
        GRAPH_ANALYTICS_CLUSTERS_FOUND,
        GRAPH_ANALYTICS_CENTRALITY_CALCULATED,
    )
except ImportError:
    class MockHistogram:
        def observe(self, *args, **kwargs): pass

    class MockCounter:
        def inc(self, *args, **kwargs): pass

    GRAPH_ANALYTICS_COMPUTATION_TIME = MockHistogram()
    GRAPH_ANALYTICS_CLUSTERS_FOUND = MockCounter()
    GRAPH_ANALYTICS_CENTRALITY_CALCULATED = MockCounter()

logger = logging.getLogger(__name__)


class AdvancedGraphAnalytics:
    """
    Erweiterte Graph-Analysen für Blockchain-Forensics
    """

    def __init__(self):
        self.graph_cache: Dict[str, nx.Graph] = {}
        self.cache_ttl = 3600  # 1 Stunde Cache

    async def detect_communities_louvain(
        self,
        addresses: List[str],
        chains: Optional[List[str]] = None,
        max_nodes: int = 1000,
        resolution: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Führe Louvain-Community-Detection auf dem Transaktionsgraph durch

        Args:
            addresses: Liste von Start-Adressen
            chains: Chains zum Analysieren (None = alle)
            max_nodes: Maximale Anzahl Knoten im Graph
            resolution: Auflösungsparameter für Louvain (höher = kleinere Cluster)

        Returns:
            {
                "communities": [{"id": int, "members": [str], "size": int, "modularity": float}],
                "modularity": float,
                "total_nodes": int,
                "computation_time": float
            }
        """
        start_time = datetime.utcnow()

        try:
            # Baue Graph aus Neo4j oder Cache
            graph = await self._build_transaction_graph(addresses, chains, max_nodes)

            if len(graph.nodes) == 0:
                return {
                    "communities": [],
                    "modularity": 0.0,
                    "total_nodes": 0,
                    "computation_time": (datetime.utcnow() - start_time).total_seconds()
                }

            # Louvain Community Detection
            communities = list(nx.community.louvain_communities(
                graph,
                resolution=resolution,
                seed=42
            ))

            # Berechne Modularität
            modularity = nx.community.modularity(graph, communities)

            # Konvertiere zu strukturierte Ausgabe
            community_data = []
            for i, community in enumerate(communities):
                community_data.append({
                    "id": i,
                    "members": sorted(list(community)),
                    "size": len(community),
                    "modularity": modularity
                })

            # Sortiere nach Größe (größte zuerst)
            community_data.sort(key=lambda x: x["size"], reverse=True)

            result = {
                "communities": community_data,
                "modularity": modularity,
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
                "computation_time": (datetime.utcnow() - start_time).total_seconds()
            }

            # Update metrics
            try:
                GRAPH_ANALYTICS_COMPUTATION_TIME.observe(result["computation_time"])
                GRAPH_ANALYTICS_CLUSTERS_FOUND.inc(len(community_data))
            except Exception:
                pass

            logger.info(f"Louvain detected {len(community_data)} communities with modularity {modularity:.3f}")
            return result

        except Exception as e:
            logger.error(f"Error in Louvain community detection: {e}")
            return {
                "communities": [],
                "modularity": 0.0,
                "total_nodes": 0,
                "computation_time": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e)
            }

    async def calculate_centrality_measures(
        self,
        addresses: List[str],
        chains: Optional[List[str]] = None,
        max_nodes: int = 1000,
        measures: List[str] = ["degree", "betweenness", "closeness"],
    ) -> Dict[str, Any]:
        """
        Berechne Zentralitätsmaße für Adressen

        Args:
            addresses: Liste von Start-Adressen
            chains: Chains zum Analysieren
            max_nodes: Maximale Anzahl Knoten
            measures: Liste gewünschter Maße

        Returns:
            {
                "centrality": {
                    "address": {
                        "degree": float,
                        "betweenness": float,
                        "closeness": float
                    }
                },
                "top_addresses": {"degree": [str], "betweenness": [str]},
                "computation_time": float
            }
        """
        start_time = datetime.utcnow()

        try:
            # Baue Graph
            graph = await self._build_transaction_graph(addresses, chains, max_nodes)

            if len(graph.nodes) == 0:
                return {
                    "centrality": {},
                    "top_addresses": {},
                    "computation_time": (datetime.utcnow() - start_time).total_seconds()
                }

            centrality_results = {}
            top_addresses = {}

            # Degree Centrality
            if "degree" in measures:
                degree_cent = nx.degree_centrality(graph)
                top_degree = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
                top_addresses["degree"] = [addr for addr, _ in top_degree]
                centrality_results.update({addr: {"degree": cent} for addr, cent in degree_cent.items()})

            # Betweenness Centrality (nur für kleinere Graphen)
            if "betweenness" in measures and len(graph.nodes) <= 500:
                betweenness_cent = nx.betweenness_centrality(graph)
                top_betweenness = sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:10]
                top_addresses["betweenness"] = [addr for addr, _ in top_betweenness]
                centrality_results = {addr: {**centrality_results.get(addr, {}), "betweenness": cent}
                                    for addr, cent in betweenness_cent.items()}

            # Closeness Centrality
            if "closeness" in measures:
                closeness_cent = nx.closeness_centrality(graph)
                top_closeness = sorted(closeness_cent.items(), key=lambda x: x[1], reverse=True)[:10]
                top_addresses["closeness"] = [addr for addr, _ in top_closeness]
                centrality_results = {addr: {**centrality_results.get(addr, {}), "closeness": cent}
                                    for addr, cent in closeness_cent.items()}

            result = {
                "centrality": centrality_results,
                "top_addresses": top_addresses,
                "computation_time": (datetime.utcnow() - start_time).total_seconds()
            }

            # Update metrics
            try:
                GRAPH_ANALYTICS_COMPUTATION_TIME.observe(result["computation_time"])
                GRAPH_ANALYTICS_CENTRALITY_CALCULATED.inc()
            except Exception:
                pass

            return result

        except Exception as e:
            logger.error(f"Error calculating centrality: {e}")
            return {
                "centrality": {},
                "top_addresses": {},
                "computation_time": (datetime.utcnow() - start_time).total_seconds(),
                "error": str(e)
            }

    async def analyze_graph_structure(
        self,
        addresses: List[str],
        chains: Optional[List[str]] = None,
        max_nodes: int = 1000,
    ) -> Dict[str, Any]:
        """
        Analysiere grundlegende Graph-Struktur

        Returns:
            {
                "nodes": int,
                "edges": int,
                "density": float,
                "avg_degree": float,
                "diameter": float,
                "avg_clustering": float,
                "components": int,
                "largest_component": int
            }
        """
        start_time = datetime.utcnow()

        try:
            graph = await self._build_transaction_graph(addresses, chains, max_nodes)

            if len(graph.nodes) == 0:
                return {
                    "nodes": 0,
                    "edges": 0,
                    "density": 0.0,
                    "avg_degree": 0.0,
                    "diameter": 0.0,
                    "avg_clustering": 0.0,
                    "components": 0,
                    "largest_component": 0,
                    "computation_time": (datetime.utcnow() - start_time).total_seconds()
                }

            # Grundlegende Metriken
            nodes = len(graph.nodes)
            edges = len(graph.edges)
            density = nx.density(graph)
            avg_degree = sum(dict(graph.degree()).values()) / nodes

            # Diameter (nur für zusammenhängende Graphen)
            diameter = 0.0
            if nx.is_connected(graph):
                try:
                    diameter = nx.diameter(graph)
                except:
                    diameter = 0.0

            # Clustering Coefficient
            avg_clustering = nx.average_clustering(graph)

            # Connected Components
            components = list(nx.connected_components(graph))
            largest_component = max(len(c) for c in components) if components else 0

            result = {
                "nodes": nodes,
                "edges": edges,
                "density": density,
                "avg_degree": avg_degree,
                "diameter": diameter,
                "avg_clustering": avg_clustering,
                "components": len(components),
                "largest_component": largest_component,
                "computation_time": (datetime.utcnow() - start_time).total_seconds()
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing graph structure: {e}")
            return {
                "error": str(e),
                "computation_time": (datetime.utcnow() - start_time).total_seconds()
            }

    async def _build_transaction_graph(
        self,
        addresses: List[str],
        chains: Optional[List[str]] = None,
        max_nodes: int = 1000,
    ) -> nx.Graph:
        """
        Baue Transaktionsgraph aus Neo4j oder Cache

        Returns:
            NetworkX Graph mit Adressen als Knoten und Transaktionen als Kanten
        """
        # Cache-Key für Graph
        cache_key = f"{'_'.join(sorted(addresses))}_{'_'.join(chains or ['all'])}_{max_nodes}"

        # Prüfe Cache
        if cache_key in self.graph_cache:
            cached_graph, cached_time = self.graph_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl:
                return cached_graph

        # Baue Graph aus Neo4j
        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j not available, returning empty graph")
            return nx.Graph()

        try:
            graph = nx.Graph()

            # Query für Transaktionen zwischen Adressen
            query = """
                MATCH (a:Address)-[t:TRANSACTION]-(b:Address)
                WHERE a.address IN $addresses OR b.address IN $addresses
                RETURN a.address as from_addr, b.address as to_addr,
                       t.tx_hash as tx_hash, t.value as value,
                       t.block_timestamp as timestamp
            """

            # Führe Query für jede Chain aus
            target_chains = chains or await self._get_available_chains()

            all_transactions = []
            for chain in target_chains:
                try:
                    params = {"addresses": addresses}
                    results = await neo4j_client.query_sync(query, params)
                    for row in results:
                        all_transactions.append({
                            "from_addr": row["from_addr"],
                            "to_addr": row["to_addr"],
                            "tx_hash": row["tx_hash"],
                            "value": float(row["value"]) if row["value"] else 0.0,
                            "timestamp": row["timestamp"],
                            "chain": chain
                        })
                except Exception as e:
                    logger.warning(f"Error querying chain {chain}: {e}")

            # Baue NetworkX Graph
            nodes_added = 0
            for tx in all_transactions:
                if nodes_added >= max_nodes:
                    break

                from_addr = tx["from_addr"]
                to_addr = tx["to_addr"]

                # Füge Knoten hinzu
                if from_addr not in graph.nodes:
                    graph.add_node(from_addr, chain=tx["chain"])
                    nodes_added += 1

                if to_addr not in graph.nodes and nodes_added < max_nodes:
                    graph.add_node(to_addr, chain=tx["chain"])
                    nodes_added += 1

                # Füge Kante hinzu (gewichtete Kante nach Transaktionswert)
                if from_addr != to_addr:  # Vermeide Self-Loops
                    weight = tx["value"] if tx["value"] > 0 else 1.0
                    if graph.has_edge(from_addr, to_addr):
                        # Erhöhe Gewicht bei mehreren Transaktionen
                        graph[from_addr][to_addr]["weight"] += weight
                    else:
                        graph.add_edge(from_addr, to_addr, weight=weight, tx_hash=tx["tx_hash"])

            # Cache Graph
            self.graph_cache[cache_key] = (graph, datetime.utcnow())

            logger.info(f"Built transaction graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
            return graph

        except Exception as e:
            logger.error(f"Error building transaction graph: {e}")
            return nx.Graph()

    async def _get_available_chains(self) -> List[str]:
        """Hole verfügbare Chains aus Neo4j"""
        if not NEO4J_AVAILABLE:
            return ["ethereum"]

        try:
            query = "MATCH (n:Address) RETURN DISTINCT n.chain as chain LIMIT 10"
            results = await neo4j_client.query_sync(query, {})
            return [row["chain"] for row in results if row["chain"]]
        except Exception:
            return ["ethereum"]

    def clear_cache(self):
        """Leere Graph-Cache"""
        self.graph_cache.clear()
        logger.info("Cleared graph analytics cache")

    async def get_cluster_insights(
        self,
        community_id: int,
        community_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analysiere einen spezifischen Cluster

        Args:
            community_id: ID des Clusters
            community_data: Cluster-Daten von detect_communities_louvain

        Returns:
            Erweiterte Insights für den Cluster
        """
        try:
            members = community_data["members"]

            # Hole detaillierte Informationen für Cluster-Mitglieder
            insights = {
                "community_id": community_id,
                "size": len(members),
                "chains": await self._get_cluster_chains(members),
                "total_volume": await self._get_cluster_volume(members),
                "risk_distribution": await self._get_cluster_risk_distribution(members),
                "bridge_activity": await self._get_cluster_bridge_activity(members),
            }

            return insights

        except Exception as e:
            logger.error(f"Error getting cluster insights: {e}")
            return {"error": str(e)}

    async def _get_cluster_chains(self, addresses: List[str]) -> List[str]:
        """Hole Chains für Cluster-Adressen"""
        if not NEO4J_AVAILABLE:
            return []

        try:
            query = """
                MATCH (a:Address)
                WHERE a.address IN $addresses
                RETURN DISTINCT a.chain as chain
            """
            results = await neo4j_client.query_sync(query, {"addresses": addresses})
            return [row["chain"] for row in results]
        except Exception:
            return []

    async def _get_cluster_volume(self, addresses: List[str]) -> float:
        """Berechne Gesamtvolumen für Cluster"""
        if not NEO4J_AVAILABLE:
            return 0.0

        try:
            query = """
                MATCH (a:Address)-[t:TRANSACTION]-(b:Address)
                WHERE a.address IN $addresses OR b.address IN $addresses
                RETURN sum(t.value) as total_volume
            """
            results = await neo4j_client.query_sync(query, {"addresses": addresses})
            return float(results[0]["total_volume"]) if results and results[0]["total_volume"] else 0.0
        except Exception:
            return 0.0

    async def _get_cluster_risk_distribution(self, addresses: List[str]) -> Dict[str, int]:
        """Hole Risk-Score-Verteilung für Cluster"""
        if not NEO4J_AVAILABLE:
            return {}

        try:
            query = """
                MATCH (a:Address)
                WHERE a.address IN $addresses AND a.risk_score IS NOT NULL
                RETURN a.risk_score as risk_score
            """
            results = await neo4j_client.query_sync(query, {"addresses": addresses})

            distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            for row in results:
                risk = float(row["risk_score"])
                if risk < 0.3:
                    distribution["low"] += 1
                elif risk < 0.7:
                    distribution["medium"] += 1
                elif risk < 0.9:
                    distribution["high"] += 1
                else:
                    distribution["critical"] += 1

            return distribution
        except Exception:
            return {}

    async def _get_cluster_bridge_activity(self, addresses: List[str]) -> Dict[str, Any]:
        """Analysiere Bridge-Aktivität im Cluster"""
        if not NEO4J_AVAILABLE:
            return {}

        try:
            query = """
                MATCH (a:Address)-[r:BRIDGE_LINK]->(b:Address)
                WHERE a.address IN $addresses OR b.address IN $addresses
                RETURN r.bridge as bridge, count(*) as count
            """
            results = await neo4j_client.query_sync(query, {"addresses": addresses})

            bridges = {}
            for row in results:
                bridge = row["bridge"]
                count = int(row["count"])
                bridges[bridge] = bridges.get(bridge, 0) + count

            return {
                "bridge_types": list(bridges.keys()),
                "bridge_activity_count": sum(bridges.values()),
                "most_active_bridge": max(bridges.items(), key=lambda x: x[1])[0] if bridges else None
            }
        except Exception:
            return {}


# Global Analytics-Instanz
advanced_graph_analytics = AdvancedGraphAnalytics()


async def detect_wallet_clusters(
    addresses: List[str],
    chains: Optional[List[str]] = None,
    algorithm: str = "louvain",
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience-Funktion für Wallet-Cluster-Erkennung

    Args:
        addresses: Liste von Adressen
        chains: Chains zum Analysieren
        algorithm: Algorithmus ("louvain", "heuristic")
        **kwargs: Zusätzliche Parameter

    Returns:
        Cluster-Ergebnisse
    """
    if algorithm == "louvain":
        return await advanced_graph_analytics.detect_communities_louvain(addresses, chains, **kwargs)
    else:
        # Fallback zu heuristischem Clustering
        from app.analytics.wallet_clustering import suggest_clusters
        return await suggest_clusters(addresses, chains or ["ethereum"], **kwargs)
