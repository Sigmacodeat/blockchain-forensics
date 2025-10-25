"""
Graph Analytics API Endpoints

Erweiterte Graph-Analysen:
- Community Detection
- Centrality Analysis  
- Pattern Detection
- Network Statistics
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.analytics.graph_analytics_service import graph_analytics_service
from app.analytics.pattern_detector import pattern_detector
from app.analytics.network_stats import network_stats
from app.auth.dependencies import get_current_user_strict, require_plan
from app.services.usage_service import check_and_consume_credits
from app.services.tenant_service import tenant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph-analytics", tags=["Graph Analytics"])


# Request/Response Models
class CommunityDetectionRequest(BaseModel):
    trace_id: Optional[str] = Field(None, description="Optional Trace ID to limit analysis")
    algorithm: str = Field("louvain", description="Algorithm: 'louvain' or 'label_propagation'")
    min_community_size: int = Field(3, ge=2, description="Minimum community size")
    max_iterations: int = Field(10, ge=1, le=50, description="Max iterations for label propagation")


class CentralityRequest(BaseModel):
    trace_id: Optional[str] = Field(None, description="Optional Trace ID")
    algorithm: str = Field("pagerank", description="Algorithm: 'pagerank', 'betweenness', 'closeness'")
    top_n: int = Field(20, ge=1, le=100, description="Number of top addresses")


class CircleDetectionRequest(BaseModel):
    trace_id: Optional[str] = Field(None, description="Optional Trace ID")
    min_circle_length: int = Field(3, ge=2, le=20, description="Min circle length")
    max_circle_length: int = Field(10, ge=2, le=20, description="Max circle length")
    min_total_value: float = Field(0.0, ge=0.0, description="Min total value in ETH")


class LayeringDetectionRequest(BaseModel):
    source_address: str = Field(..., description="Source address to analyze")
    max_depth: int = Field(5, ge=1, le=10, description="Maximum depth")
    min_split_count: int = Field(3, ge=2, description="Minimum splits per layer")


class SmurfPatternRequest(BaseModel):
    address: str = Field(..., description="Target address")
    time_window_hours: int = Field(24, ge=1, le=168, description="Time window in hours")
    min_tx_count: int = Field(10, ge=5, description="Minimum transaction count")
    max_tx_value: float = Field(0.1, ge=0.0, description="Maximum value per transaction")


class PeelChainRequest(BaseModel):
    source_address: str = Field(..., description="Source address")
    min_chain_length: int = Field(5, ge=3, description="Minimum chain length")
    peel_percentage: float = Field(0.9, ge=0.5, le=1.0, description="Peel percentage threshold")


class RapidMovementRequest(BaseModel):
    address: str = Field(..., description="Source address")
    max_time_seconds: int = Field(300, ge=10, le=3600, description="Max time between hops")
    min_hops: int = Field(3, ge=2, description="Minimum number of hops")


# Community Detection Endpoints
@router.post("/communities/detect")
async def detect_communities(request: CommunityDetectionRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Führt Community Detection auf dem Transaction Graph durch.
    
    **Algorithmen:**
    - `louvain`: Modularity-basierte Community Detection (empfohlen)
    - `label_propagation`: Schnellere Alternative für große Graphen
    
    **Returns:**
    - Communities mit Mitgliedern, Größe, Risiko-Statistiken
    """
    try:
        # Credits: communities detection is moderately expensive
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            # ✅ FIX: Plan aus Token
            plan_id = current_user.get('plan', 'community')
            amount = max(5, min(50, 5 + int(request.max_iterations) + int(request.min_community_size/2)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_communities")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Community Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await graph_analytics_service.detect_communities(
            trace_id=request.trace_id,
            algorithm=request.algorithm,
            min_community_size=request.min_community_size,
            max_iterations=request.max_iterations
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(status_code=500, detail="Community detection failed")


# Centrality Endpoints
@router.post("/centrality/calculate")
async def calculate_centrality(request: CentralityRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Berechnet Centrality Metrics für Adressen.
    
    **Algorithmen:**
    - `pagerank`: Identifiziert wichtige Hubs (empfohlen)
    - `betweenness`: Findet Broker-Adressen
    - `closeness`: Misst zentrale Position im Netzwerk
    
    **Returns:**
    - Top-N Adressen mit Scores und Metadaten
    """
    try:
        # Credits: centrality cost scales with top_n
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            # ✅ FIX: Plan aus Token
            plan_id = current_user.get('plan', 'community')
            amount = max(3, min(40, int((request.top_n or 20) / 5)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason=f"graph_centrality_{request.algorithm}")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Centrality Analyse")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await graph_analytics_service.calculate_centrality(
            trace_id=request.trace_id,
            algorithm=request.algorithm,
            top_n=request.top_n
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Centrality calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Centrality calculation failed")


@router.get("/centrality/pagerank")
async def get_pagerank(
    trace_id: Optional[str] = Query(None),
    top_n: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Schneller Zugriff auf PageRank Centrality.
    
    **Use Case:** Findet einflussreichste Adressen im Netzwerk
    """
    try:
        # Credits: lighter for pagerank
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(2, min(20, int(top_n/10) + 2))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pagerank")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für PageRank")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await graph_analytics_service.calculate_centrality(
            trace_id=trace_id,
            algorithm="pagerank",
            top_n=top_n
        )
        return result
    except Exception as e:
        logger.error(f"PageRank failed: {e}")
        # Return default stats if service fails
        return {
            "top_addresses": [],
            "top_scores": [],
            "top_address_metadata": []
        }


# Network Statistics Endpoints
@router.get("/stats/network")
async def get_network_statistics(
    trace_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Berechnet grundlegende Netzwerk-Statistiken.
    
    **Returns:**
    - Nodes, Edges, Density, Avg Degree
    """
    try:
        # Credits: light
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = 3
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_network_stats")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Netzwerk-Statistiken")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await graph_analytics_service.get_network_statistics(trace_id=trace_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Network stats failed: {e}")
        # Return default stats if service fails
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "network_density": 0.0,
            "communities_detected": 0,
            "high_risk_clusters": 0,
            "avg_degree": 0.0
        }


@router.get("/stats/degree-distribution")
async def get_degree_distribution(
    trace_id: Optional[str] = Query(None),
    direction: str = Query("both", pattern="^(in|out|both)$"),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Berechnet Degree Distribution.
    
    **Parameters:**
    - `direction`: "in" (incoming), "out" (outgoing), "both"
    
    **Returns:**
    - Distribution, Avg Degree, Max Degree
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = 4
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_degree_distribution")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Degree Distribution")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_degree_distribution(
            trace_id=trace_id,
            direction=direction
        )
        return result
    except Exception as e:
        logger.error(f"Degree distribution failed: {e}")
        raise HTTPException(status_code=500, detail="Degree distribution failed")


@router.get("/stats/clustering")
async def get_clustering_coefficient(
    trace_id: Optional[str] = Query(None),
    sample_size: Optional[int] = Query(None, ge=100, le=10000),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Berechnet Clustering Coefficients.
    
    **Returns:**
    - Local & Global Clustering Coefficients
    - Misst "Cliquishness" des Netzwerks
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(3, min(20, int((sample_size or 100)/500)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_clustering")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Clustering")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_clustering_coefficient(
            trace_id=trace_id,
            sample_size=sample_size
        )
        return result
    except Exception as e:
        logger.error(f"Clustering coefficient failed: {e}")
        raise HTTPException(status_code=500, detail="Clustering coefficient failed")


@router.get("/stats/path-length")
async def get_path_length_distribution(
    trace_id: Optional[str] = Query(None),
    max_length: int = Query(6, ge=2, le=10),
    sample_pairs: int = Query(100, ge=10, le=1000),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Analysiert Pfadlängen zwischen Node-Paaren.
    
    **Returns:**
    - Path Length Distribution
    - Average Path Length
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(4, min(30, int(sample_pairs/50) + int(max_length/2)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_path_length")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Pfadlängen-Analyse")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_path_length_distribution(
            trace_id=trace_id,
            max_length=max_length,
            sample_pairs=sample_pairs
        )
        return result
    except Exception as e:
        logger.error(f"Path length distribution failed: {e}")
        raise HTTPException(status_code=500, detail="Path length distribution failed")


@router.get("/stats/components")
async def get_connected_components(
    trace_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Findet schwach verbundene Komponenten.
    
    **Returns:**
    - Liste der Components mit Größen
    - Identifiziert isolierte Sub-Netzwerke
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = 4
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_connected_components")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Komponenten-Analyse")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_connected_components(trace_id=trace_id)
        return result
    except Exception as e:
        logger.error(f"Connected components failed: {e}")
        raise HTTPException(status_code=500, detail="Connected components failed")


@router.get("/stats/temporal")
async def get_temporal_metrics(
    time_window_hours: int = Query(24, ge=1, le=168),
    bucket_size_hours: int = Query(1, ge=1, le=24),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Berechnet zeitbasierte Netzwerk-Metriken.
    
    **Returns:**
    - Transactions per Time Bucket
    - Peak Activity Periods
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(3, min(15, int(time_window_hours/24) + 2))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_temporal")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für temporale Metriken")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_temporal_metrics(
            time_window_hours=time_window_hours,
            bucket_size_hours=bucket_size_hours
        )
        return result
    except Exception as e:
        logger.error(f"Temporal metrics failed: {e}")
        raise HTTPException(status_code=500, detail="Temporal metrics failed")


@router.get("/stats/hubs")
async def get_hub_analysis(
    trace_id: Optional[str] = Query(None),
    min_degree: int = Query(10, ge=5),
    top_n: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_strict),
):
    """
    Identifiziert Hub-Nodes (hoher Degree).
    
    **Returns:**
    - Top Hubs mit Degree-Statistiken
    - Risiko-Level der Hubs
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(3, min(25, int(top_n/5)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_hubs")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Hub-Analyse")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await network_stats.get_hub_analysis(
            trace_id=trace_id,
            min_degree=min_degree,
            top_n=top_n
        )
        return result
    except Exception as e:
        logger.error(f"Hub analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Hub analysis failed")


# Pattern Detection Endpoints
@router.post("/patterns/circles")
async def detect_circles(request: CircleDetectionRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Erkennt zirkuläre Transaktionsketten (potenzielle Geldwäsche).
    
    **Use Case:**
    - Identifiziert Round-Trip Transaktionen
    - Findet Layering-Strukturen
    
    **Returns:**
    - Detected Circles mit Risk Scores
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(6, min(30, int((request.max_circle_length or 6))))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pattern_circles")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Circle Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await pattern_detector.detect_circles(
            trace_id=request.trace_id,
            min_circle_length=request.min_circle_length,
            max_circle_length=request.max_circle_length,
            min_total_value=request.min_total_value
        )
        return result
    except Exception as e:
        logger.error(f"Circle detection failed: {e}")
        raise HTTPException(status_code=500, detail="Circle detection failed")


@router.post("/patterns/layering")
async def detect_layering(request: LayeringDetectionRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Erkennt Layering Schemes (komplexe Splitting-Strukturen).
    
    **Use Case:**
    - Findet Multi-Layer Obfuscation
    - Identifiziert strukturierte Geldwäsche
    
    **Returns:**
    - Layering Structure mit Risk Assessment
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(8, min(40, int(request.max_depth) + int(request.min_split_count)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pattern_layering")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Layering Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await pattern_detector.detect_layering(
            source_address=request.source_address,
            max_depth=request.max_depth,
            min_split_count=request.min_split_count
        )
        return result
    except Exception as e:
        logger.error(f"Layering detection failed: {e}")
        raise HTTPException(status_code=500, detail="Layering detection failed")


@router.post("/patterns/smurfing")
async def detect_smurf_patterns(request: SmurfPatternRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Erkennt Smurfing (viele kleine Transaktionen).
    
    **Use Case:**
    - Identifiziert Structuring zur AML-Umgehung
    - Findet koordinierte Kleinbeträge
    
    **Returns:**
    - Detected Smurf Patterns mit Risk Scores
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(5, min(30, int(request.min_tx_count/5) + 2))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pattern_smurf")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Smurf Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await pattern_detector.detect_smurf_patterns(
            address=request.address,
            time_window_hours=request.time_window_hours,
            min_tx_count=request.min_tx_count,
            max_tx_value=request.max_tx_value
        )
        return result
    except Exception as e:
        logger.error(f"Smurf pattern detection failed: {e}")
        raise HTTPException(status_code=500, detail="Smurf pattern detection failed")


@router.post("/patterns/peel-chains")
async def detect_peel_chains(request: PeelChainRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Erkennt Peel Chains (schrittweiser Abbau).
    
    **Use Case:**
    - Identifiziert systematischen Funds-Abbau
    - Findet Tumbler-ähnliche Strukturen
    
    **Returns:**
    - Detected Peel Chains mit Risk Scores
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(6, min(35, int(request.min_chain_length/2) + 5))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pattern_peel")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Peel Chain Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await pattern_detector.detect_peel_chains(
            source_address=request.source_address,
            min_chain_length=request.min_chain_length,
            peel_percentage=request.peel_percentage
        )
        return result
    except Exception as e:
        logger.error(f"Peel chain detection failed: {e}")
        raise HTTPException(status_code=500, detail="Peel chain detection failed")


@router.post("/patterns/rapid-movement")
async def detect_rapid_movement(request: RapidMovementRequest, current_user: dict = Depends(require_plan('pro'))):
    """
    Erkennt schnelle Geldbewegungen (potenzielle Flucht).
    
    **Use Case:**
    - Identifiziert Panic-Bewegungen
    - Findet automatisierte Transfers
    
    **Returns:**
    - Detected Rapid Movements mit Speed Metrics
    """
    try:
        try:
            tenant_id = str(current_user["user_id"])  # simplified tenant
            plan_id = tenant_service.get_plan_id(tenant_id)
            amount = max(5, min(25, int(request.min_hops) + int(request.max_time_seconds/600)))
            allowed = await check_and_consume_credits(tenant_id, plan_id, amount, reason="graph_pattern_rapid")
            if not allowed:
                raise HTTPException(status_code=402, detail="Nicht genügend Credits für Rapid-Movement Detection")
        except HTTPException:
            raise
        except Exception:
            pass

        result = await pattern_detector.detect_rapid_movement(
            address=request.address,
            max_time_seconds=request.max_time_seconds,
            min_hops=request.min_hops
        )
        return result
    except Exception as e:
        logger.error(f"Rapid movement detection failed: {e}")
        raise HTTPException(status_code=500, detail="Rapid movement detection failed")


# Combined Analysis Endpoint
@router.get("/analyze/{address}")
async def comprehensive_analysis(
    address: str,
    include_patterns: bool = Query(True, description="Include pattern detection"),
    include_centrality: bool = Query(True, description="Include centrality analysis")
):
    """
    Führt umfassende Graph-Analyse für eine Adresse durch.
    
    **Returns:**
    - Community Membership
    - Centrality Scores
    - Detected Patterns
    - Network Statistics
    """
    try:
        results = {
            "address": address,
            "timestamp": None,
            "analysis": {}
        }
        
        # Centrality
        if include_centrality:
            try:
                pagerank = await graph_analytics_service.calculate_centrality(
                    algorithm="pagerank",
                    top_n=100
                )
                # Find address in results
                for addr_data in pagerank["top_addresses"]:
                    if addr_data["address"].lower() == address.lower():
                        results["analysis"]["centrality"] = {
                            "pagerank_score": addr_data["score"],
                            "rank": pagerank["top_addresses"].index(addr_data) + 1
                        }
                        break
            except:
                pass
        
        # Pattern Detection
        if include_patterns:
            try:
                # Check for circles involving this address
                circles = await pattern_detector.detect_circles(min_circle_length=3, max_circle_length=8)
                address_circles = [
                    c for c in circles["detected"] 
                    if address.lower() in [a.lower() for a in c["addresses"]]
                ]
                if address_circles:
                    results["analysis"]["circles"] = {
                        "count": len(address_circles),
                        "max_risk_score": max(c["risk_score"] for c in address_circles)
                    }
            except:
                pass
        
        # Network Stats
        try:
            # Get degree for this address
            query = """
            MATCH (a:Address {address: $address})
            RETURN size((a)-[:TRANSACTION]->()) as out_degree,
                   size((a)<-[:TRANSACTION]-()) as in_degree
            """
            from app.db.neo4j_client import neo4j_client
            async with neo4j_client.get_session() as session:
                result = await session.run(query, {"address": address.lower()})
                record = await result.single()
                if record:
                    results["analysis"]["degree"] = {
                        "in": record["in_degree"],
                        "out": record["out_degree"],
                        "total": record["in_degree"] + record["out_degree"]
                    }
        except:
            pass
        
        return results
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Comprehensive analysis failed")
