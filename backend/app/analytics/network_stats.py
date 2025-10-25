"""
Network Statistics Module

Erweiterte Statistiken für Transaction Networks:
- Degree Distribution
- Clustering Coefficients
- Path Length Analysis
- Component Analysis
- Time-based Metrics
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from app.db.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class NetworkStats:
    """Service für Netzwerk-Statistiken"""
    
    def __init__(self):
        self.client = neo4j_client
        
    async def get_degree_distribution(
        self,
        trace_id: Optional[str] = None,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """
        Berechnet Degree Distribution des Netzwerks.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            direction: "in", "out" oder "both"
            
        Returns:
            Dict mit distribution und statistics
        """
        try:
            if direction == "in":
                degree_expr = "size((a)<-[:TRANSACTION]-())"
            elif direction == "out":
                degree_expr = "size((a)-[:TRANSACTION]->())"
            else:  # both
                degree_expr = "size((a)-[:TRANSACTION]-())"
            
            if trace_id:
                query = f"""
                MATCH (t:Trace {{trace_id: '{trace_id}'}})-[:INCLUDES]->(a:Address)
                WITH a, {degree_expr} as degree
                RETURN degree, count(*) as count
                ORDER BY degree
                """
            else:
                query = f"""
                MATCH (a:Address)
                WITH a, {degree_expr} as degree
                RETURN degree, count(*) as count
                ORDER BY degree
                """
            
            session = self.client.driver.session()
            result = await session.run(query)
            distribution = []
            total_nodes = 0
            
            async for record in result:
                distribution.append({
                    "degree": record["degree"],
                    "count": record["count"]
                })
                total_nodes += record["count"]

            # Calculate statistics
            degrees = [d["degree"] for d in distribution for _ in range(d["count"])]
            avg_degree = sum(degrees) / len(degrees) if degrees else 0
            max_degree = max(degrees) if degrees else 0
            
            out = {
                "direction": direction,
                "trace_id": trace_id,
                "distribution": distribution,
                "statistics": {
                    "total_nodes": total_nodes,
                    "avg_degree": round(avg_degree, 2),
                    "max_degree": max_degree,
                    "isolated_nodes": distribution[0]["count"] if distribution and distribution[0]["degree"] == 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await session.close()
            except Exception:
                pass
            return out
                
        except Exception as e:
            logger.error(f"Degree distribution calculation failed: {e}")
            raise
    
    async def get_clustering_coefficient(
        self,
        trace_id: Optional[str] = None,
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Berechnet lokale und globale Clustering Coefficients.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            sample_size: Optional - begrenzt Anzahl der analysierten Nodes
            
        Returns:
            Dict mit clustering coefficients
        """
        try:
            # Verwende Neo4j GDS für effiziente Berechnung
            query = """
            CALL gds.graph.project(
                'clusteringGraph',
                'Address',
                {
                    TRANSACTION: {
                        orientation: 'UNDIRECTED'
                    }
                }
            )
            YIELD graphName
            
            CALL gds.localClusteringCoefficient.stream('clusteringGraph')
            YIELD nodeId, localClusteringCoefficient
            MATCH (a:Address) WHERE id(a) = nodeId
            RETURN a.address as address,
                   localClusteringCoefficient as coefficient
            ORDER BY coefficient DESC
            LIMIT $limit
            """
            
            limit = sample_size or 1000
            
            async with self.client.get_session() as session:
                result = await session.run(query, limit=limit)
                coefficients = []
                
                async for record in result:
                    coefficients.append({
                        "address": record["address"],
                        "coefficient": float(record["coefficient"])
                    })
                
                # Cleanup graph
                await session.run("CALL gds.graph.drop('clusteringGraph') YIELD graphName")
                
                # Calculate global coefficient
                global_coeff = sum(c["coefficient"] for c in coefficients) / len(coefficients) if coefficients else 0
                
                return {
                    "trace_id": trace_id,
                    "local_coefficients": coefficients[:20],  # Top 20
                    "statistics": {
                        "global_coefficient": round(global_coeff, 4),
                        "sample_size": len(coefficients),
                        "max_coefficient": max([c["coefficient"] for c in coefficients]) if coefficients else 0
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Clustering coefficient calculation failed: {e}")
            # Cleanup on error
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('clusteringGraph') YIELD graphName")
            except:
                pass
            raise
    
    async def get_path_length_distribution(
        self,
        trace_id: Optional[str] = None,
        max_length: int = 6,
        sample_pairs: int = 100
    ) -> Dict[str, Any]:
        """
        Analysiert Pfadlängen zwischen Node-Paaren.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            max_length: Maximale Pfadlänge
            sample_pairs: Anzahl zufälliger Paare
            
        Returns:
            Dict mit path length statistics
        """
        try:
            query = f"""
            MATCH (a1:Address), (a2:Address)
            WHERE id(a1) < id(a2)
            WITH a1, a2
            LIMIT {sample_pairs}
            MATCH path = shortestPath((a1)-[:TRANSACTION*1..{max_length}]-(a2))
            RETURN length(path) as path_length, count(*) as count
            ORDER BY path_length
            """
            
            async with self.client.get_session() as session:
                result = await session.run(query)
                distribution = []
                
                async for record in result:
                    distribution.append({
                        "length": record["path_length"],
                        "count": record["count"]
                    })
                
                # Calculate avg path length
                total_paths = sum(d["count"] for d in distribution)
                avg_length = sum(d["length"] * d["count"] for d in distribution) / total_paths if total_paths > 0 else 0
                
                return {
                    "trace_id": trace_id,
                    "distribution": distribution,
                    "statistics": {
                        "avg_path_length": round(avg_length, 2),
                        "max_observed_length": max([d["length"] for d in distribution]) if distribution else 0,
                        "total_paths_analyzed": total_paths,
                        "sample_pairs": sample_pairs
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Path length distribution failed: {e}")
            raise
    
    async def get_connected_components(
        self,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Findet schwach verbundene Komponenten im Netzwerk.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            
        Returns:
            Dict mit component information
        """
        try:
            query = """
            CALL gds.graph.project(
                'componentGraph',
                'Address',
                {
                    TRANSACTION: {
                        orientation: 'UNDIRECTED'
                    }
                }
            )
            YIELD graphName
            
            CALL gds.wcc.stream('componentGraph')
            YIELD nodeId, componentId
            MATCH (a:Address) WHERE id(a) = nodeId
            RETURN componentId, collect(a.address) as members, count(*) as size
            ORDER BY size DESC
            LIMIT 20
            """
            
            async with self.client.get_session() as session:
                result = await session.run(query)
                components = []
                total_components = 0
                
                async for record in result:
                    components.append({
                        "component_id": record["componentId"],
                        "size": record["size"],
                        "sample_members": record["members"][:10]  # Nur Top 10 Adressen
                    })
                    total_components += 1
                
                # Cleanup
                await session.run("CALL gds.graph.drop('componentGraph') YIELD graphName")
                
                return {
                    "trace_id": trace_id,
                    "components": components,
                    "statistics": {
                        "total_components": total_components,
                        "largest_component_size": components[0]["size"] if components else 0,
                        "isolated_nodes": len([c for c in components if c["size"] == 1])
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Connected components analysis failed: {e}")
            try:
                async with self.client.get_session() as session:
                    await session.run("CALL gds.graph.drop('componentGraph') YIELD graphName")
            except:
                pass
            raise
    
    async def get_temporal_metrics(
        self,
        time_window_hours: int = 24,
        bucket_size_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Berechnet zeitbasierte Netzwerk-Metriken.
        
        Args:
            time_window_hours: Zeitfenster in Stunden
            bucket_size_hours: Bucket-Größe für Aggregation
            
        Returns:
            Dict mit temporal statistics
        """
        try:
            now = datetime.utcnow()
            start_time = now - timedelta(hours=time_window_hours)
            
            query = """
            MATCH ()-[tx:TRANSACTION]->()
            WHERE tx.timestamp >= $start_time
            WITH tx, 
                 duration.inHours(
                     datetime($start_time), 
                     datetime(tx.timestamp)
                 ).hours / $bucket_size as bucket
            WITH floor(bucket) as time_bucket,
                 count(tx) as tx_count,
                 avg(tx.value) as avg_value,
                 sum(tx.value) as total_value
            RETURN time_bucket,
                   tx_count,
                   avg_value,
                   total_value
            ORDER BY time_bucket
            """
            
            async with self.client.get_session() as session:
                result = await session.run(
                    query,
                    start_time=start_time.isoformat(),
                    bucket_size=bucket_size_hours
                )
                
                buckets = []
                async for record in result:
                    bucket_start = start_time + timedelta(hours=record["time_bucket"] * bucket_size_hours)
                    buckets.append({
                        "timestamp": bucket_start.isoformat(),
                        "tx_count": record["tx_count"],
                        "avg_value": float(record["avg_value"]),
                        "total_value": float(record["total_value"])
                    })
                
                # Calculate peak activity
                peak_bucket = max(buckets, key=lambda b: b["tx_count"]) if buckets else None
                
                return {
                    "time_window_hours": time_window_hours,
                    "bucket_size_hours": bucket_size_hours,
                    "buckets": buckets,
                    "statistics": {
                        "total_transactions": sum(b["tx_count"] for b in buckets),
                        "total_volume": sum(b["total_value"] for b in buckets),
                        "peak_activity": {
                            "timestamp": peak_bucket["timestamp"] if peak_bucket else None,
                            "tx_count": peak_bucket["tx_count"] if peak_bucket else 0
                        },
                        "avg_tx_per_hour": sum(b["tx_count"] for b in buckets) / len(buckets) if buckets else 0
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Temporal metrics calculation failed: {e}")
            raise
    
    async def get_hub_analysis(
        self,
        trace_id: Optional[str] = None,
        min_degree: int = 10,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Identifiziert Hub-Nodes (hoher Degree) im Netzwerk.
        
        Args:
            trace_id: Optional - beschränkt auf Trace
            min_degree: Minimaler Degree für Hubs
            top_n: Anzahl Top Hubs
            
        Returns:
            Dict mit hub information
        """
        try:
            query = """
            MATCH (a:Address)
            WITH a,
                 size((a)-[:TRANSACTION]->()) as out_degree,
                 size((a)<-[:TRANSACTION]-()) as in_degree
            WHERE out_degree + in_degree >= $min_degree
            WITH a, out_degree, in_degree, (out_degree + in_degree) as total_degree
            ORDER BY total_degree DESC
            LIMIT $top_n
            RETURN a.address as address,
                   out_degree,
                   in_degree,
                   total_degree,
                   a.labels as labels,
                   a.risk_level as risk_level
            """
            
            session = self.client.driver.session()
            result = await session.run(query, min_degree=min_degree, top_n=top_n)
            hubs = []
            
            async for record in result:
                hubs.append({
                    "address": record["address"],
                    "out_degree": record["out_degree"],
                    "in_degree": record["in_degree"],
                    "total_degree": record["total_degree"],
                    "labels": record.get("labels", []),
                    "risk_level": record.get("risk_level", "UNKNOWN")
                })

            out = {
                "trace_id": trace_id,
                "hubs": hubs,
                "statistics": {
                    "total_hubs": len(hubs),
                    "avg_degree": sum(h["total_degree"] for h in hubs) / len(hubs) if hubs else 0,
                    "max_degree": max([h["total_degree"] for h in hubs]) if hubs else 0,
                    "high_risk_hubs": len([h for h in hubs if h["risk_level"] in ["HIGH", "CRITICAL"]])
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await session.close()
            except Exception:
                pass
            return out
                
        except Exception as e:
            logger.error(f"Hub analysis failed: {e}")
            raise


# Singleton instance
network_stats = NetworkStats()
