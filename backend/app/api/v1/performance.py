import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

"""
Performance Monitoring API
==========================

Query optimization, cache stats, and performance metrics
"""

from app.performance.query_optimizer import query_optimizer
from app.performance.cache_manager import cache_manager
from app.performance.batch_processor import batch_processor
from app.services.performance_monitor import performance_monitor, performance_tracer

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== Response Models =====

class QueryStats(BaseModel):
    """Query statistics"""
    total_queries: int
    slow_queries: int
    cached_queries: int
    total_time_ms: float
    average_time_ms: float
    slow_query_rate: float


class CacheStats(BaseModel):
    """Cache statistics"""
    hits: int
    misses: int
    local_hits: int
    redis_hits: int
    sets: int
    deletes: int
    evictions: int
    total_requests: int
    hit_rate: float
    local_cache_size: int
    local_cache_hit_rate: float


class BatchStats(BaseModel):
    """Batch processing statistics"""
    batches_processed: int
    items_processed: int
    errors: int
    avg_batch_time_ms: float
    queue_sizes: Dict[str, int]


class SystemHealth(BaseModel):
    """System health metrics"""
    status: str
    uptime: int
    version: str
    timestamp: str
    system: Dict[str, Any]
    database: Dict[str, Any]
    services: Dict[str, bool]
    environment: Dict[str, Any]


# ===== New Monitoring Endpoints =====

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health() -> Dict[str, Any]:
    """
    Get comprehensive system health information

    Returns system status, uptime, services, and database health
    """
    try:
        import psutil
        import platform

        # Get system uptime
        boot_time = psutil.boot_time()
        uptime_seconds = datetime.now().timestamp() - boot_time

        # Check services (placeholder for now)
        services = {
            "alert_engine": True,
            "graph_db": True,
            "ml_service": True
        }

        # Overall status
        overall_status = "healthy"
        if not all(services.values()):
            overall_status = "degraded"

        health_data = {
            "status": overall_status,
            "uptime": int(uptime_seconds),
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/')._asdict()
            },
            "database": {
                "connected": True,
                "response_time": 50,
                "type": "Neo4j + PostgreSQL"
            },
            "services": services,
            "environment": {
                "mode": "production",
                "debug": False,
                "log_level": "INFO"
            }
        }

        return health_data

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/metrics")
async def get_monitoring_metrics(
    time_window_minutes: int = Query(60, ge=1, le=1440),
    metric_filter: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get performance monitoring metrics

    **Query Parameters:**
    - time_window_minutes: Time window for metrics (1-1440 minutes)
    - metric_filter: Optional filter for specific metrics
    """
    try:
        summary = performance_monitor.get_metrics_summary(time_window_minutes)

        if metric_filter:
            if metric_filter in summary["metrics"]:
                summary["metrics"] = {metric_filter: summary["metrics"][metric_filter]}
            else:
                summary["metrics"] = {}

        return summary

    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/slo")
async def get_slo_report() -> Dict[str, Any]:
    """
    Get SLO compliance report
    """
    try:
        report = performance_monitor.get_slo_report()
        return report

    except Exception as e:
        logger.error(f"Error getting SLO report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/traces")
async def get_trace_summary() -> Dict[str, Any]:
    """
    Get distributed tracing summary
    """
    try:
        summary = performance_tracer.get_trace_summary()
        return summary

    except Exception as e:
        logger.error(f"Error getting trace summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/record")
async def record_custom_metric(
    name: str = Query(...),
    value: float = Query(...),
    tags: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Record a custom performance metric

    **Query Parameters:**
    - name: Name of the metric
    - value: Numeric value of the metric
    - tags: Optional tags in format "key1:value1,key2:value2"
    """
    try:
        # Parse tags
        parsed_tags = {}
        if tags:
            for tag_pair in tags.split(","):
                if ":" in tag_pair:
                    key, value = tag_pair.split(":", 1)
                    parsed_tags[key.strip()] = value.strip()

        performance_monitor.record_metric(name, value, parsed_tags)

        return {
            "status": "recorded",
            "metric": name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error recording custom metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/dashboard")
async def get_performance_dashboard() -> Dict[str, Any]:
    """
    Get comprehensive performance dashboard data
    """
    try:
        # Get all performance data
        metrics_summary = performance_monitor.get_metrics_summary(60)  # Last hour
        slo_report = performance_monitor.get_slo_report()
        trace_summary = performance_tracer.get_trace_summary()

        # Get system metrics
        import psutil
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)

        dashboard = {
            "generated_at": datetime.utcnow().isoformat(),
            "system_health": {
                "status": "healthy",
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "performance_metrics": metrics_summary,
            "slo_compliance": slo_report,
            "distributed_tracing": trace_summary,
            "recent_alerts": performance_monitor.alerts[-10:],  # Last 10 alerts
            "key_indicators": {
                "avg_response_time_ms": metrics_summary["metrics"].get("api_response_time", {}).get("avg", 0),
                "error_rate_percent": 0,  # Would calculate from error metrics
                "throughput_rps": 0,  # Would calculate from request metrics
                "uptime_percentage": 99.9  # Placeholder
            }
        }

        return dashboard

    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Response Models =====

class QueryStats(BaseModel):
    """Query statistics"""
    total_queries: int
    slow_queries: int
    cached_queries: int
    total_time_ms: float
    average_time_ms: float
    slow_query_rate: float


class CacheStats(BaseModel):
    """Cache statistics"""
    hits: int
    misses: int
    local_hits: int
    redis_hits: int
    sets: int
    deletes: int
    evictions: int
    total_requests: int
    hit_rate: float
    local_cache_size: int
    local_cache_hit_rate: float


class BatchStats(BaseModel):
    """Batch processing statistics"""
    batches_processed: int
    items_processed: int
    errors: int
    avg_batch_time_ms: float
    queue_sizes: Dict[str, int]


# ===== API Endpoints =====

# ===== Request Models =====
class ExplainIn(BaseModel):
    query: str

@router.get("/query-stats", response_model=QueryStats)
async def get_query_stats():
    """
    Get database query statistics
    
    Returns:
    - Total queries executed
    - Slow query count
    - Average query time
    - Slow query rate
    """
    try:
        stats = query_optimizer.get_query_stats()
        return QueryStats(**stats)
    
    except Exception as e:
        logger.error(f"Get query stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/neo4j")
async def explain_neo4j(payload: ExplainIn):
    """
    Return a minimal EXPLAIN plan for a Neo4j Cypher query (PoC; simulated plan)
    """
    try:
        return await query_optimizer.explain_neo4j(payload.query)
    except Exception as e:
        logger.error(f"Neo4j explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/postgres")
async def explain_postgres(payload: ExplainIn):
    """
    Return a minimal EXPLAIN plan for a Postgres SQL query (PoC; simulated plan)
    """
    try:
        return await query_optimizer.explain_postgres(payload.query)
    except Exception as e:
        logger.error(f"Postgres explain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slow-queries")
async def get_slow_queries(limit: int = Query(20, ge=1, le=100)):
    """
    Get recent slow queries
    
    **Query Parameters:**
    - limit: Number of queries to return (default: 20, max: 100)
    
    Returns list of slowest queries with:
    - Query text
    - Execution time
    - Database
    - Timestamp
    """
    try:
        slow_queries = query_optimizer.get_slow_queries(limit=limit)
        return {
            "slow_queries": slow_queries,
            "count": len(slow_queries),
            "threshold_ms": query_optimizer.slow_query_threshold_ms
        }
    
    except Exception as e:
        logger.error(f"Get slow queries failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-query")
async def optimize_query(
    query: str,
    database: str = Query("neo4j", pattern="^(neo4j|postgres)$")
):
    """
    Get query optimization recommendations
    
    **Request Body:**
    ```json
    {
      "query": "MATCH (n:Address) WHERE n.address = '0x123' RETURN n",
      "database": "neo4j"
    }
    ```
    
    **Returns:**
    - Original query
    - Optimized query (if applicable)
    - List of recommendations
    - Estimated improvement
    """
    try:
        if database == "neo4j":
            result = query_optimizer.optimize_neo4j_query(query)
        elif database == "postgres":
            result = query_optimizer.optimize_postgres_query(query)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported database: {database}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index-recommendations")
async def get_index_recommendations(
    database: str = Query("all", pattern="^(neo4j|postgres|all)$")
):
    """
    Get index recommendations based on slow queries
    
    **Query Parameters:**
    - database: Filter by database (neo4j, postgres, all)
    
    Returns:
    - List of recommended indexes
    - Impact assessment
    - Example CREATE INDEX statements
    """
    try:
        recommendations = query_optimizer.get_index_recommendations(database=database)
        
        return {
            "recommendations": recommendations,
            "total_recommendations": sum(len(r.get('indexes', [])) for r in recommendations)
        }
    
    except Exception as e:
        logger.error(f"Get index recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats", response_model=CacheStats)
async def get_cache_stats():
    """
    Get cache performance statistics
    
    Returns:
    - Cache hit/miss counts
    - Hit rate (%)
    - Local vs Redis cache performance
    - Cache size
    """
    try:
        stats = cache_manager.get_stats()
        return CacheStats(**stats)
    
    except Exception as e:
        logger.error(f"Get cache stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = Query("local", pattern="^(local|all)$")
):
    """
    Clear cache
    
    **Query Parameters:**
    - cache_type: Type to clear (local, all)
    
    **Warning:** Clearing cache will impact performance temporarily
    """
    try:
        if cache_type == "local":
            cache_manager.clear_local_cache()
            message = "Local cache cleared"
        elif cache_type == "all":
            await cache_manager.clear_all()
            message = "All caches cleared (local + Redis)"
        
        return {
            "status": "success",
            "message": message,
            "cache_type": cache_type
        }
    
    except Exception as e:
        logger.error(f"Clear cache failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/warm/{key}")
async def warm_cache(
    key: str,
    ttl_seconds: int = Query(300, ge=60, le=3600)
):
    """
    Manually warm cache for a specific key
    
    **Path Parameters:**
    - key: Cache key to warm
    
    **Query Parameters:**
    - ttl_seconds: TTL in seconds (60-3600)
    
    **Note:** This endpoint requires a loader function - 
    actual implementation would be service-specific
    """
    try:
        # This is a placeholder - actual implementation would
        # call the appropriate loader function
        
        return {
            "status": "success",
            "message": f"Cache warming initiated for key: {key}",
            "ttl_seconds": ttl_seconds
        }
    
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch-stats", response_model=BatchStats)
async def get_batch_stats():
    """
    Get batch processing statistics
    
    Returns:
    - Batches processed
    - Items processed
    - Error count
    - Average batch time
    - Current queue sizes
    """
    try:
        stats = batch_processor.get_stats()
        return BatchStats(**stats)
    
    except Exception as e:
        logger.error(f"Get batch stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/flush")
async def flush_batches():
    """
    Manually flush all pending batches
    
    Forces immediate processing of queued batch items
    """
    try:
        await batch_processor.flush_all()
        
        return {
            "status": "success",
            "message": "All batches flushed"
        }
    
    except Exception as e:
        logger.error(f"Batch flush failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary():
    """
    Get comprehensive performance summary
    
    Combines query, cache, and batch statistics
    """
    try:
        query_stats = query_optimizer.get_query_stats()
        cache_stats = cache_manager.get_stats()
        batch_stats = batch_processor.get_stats()
        
        return {
            "query_performance": query_stats,
            "cache_performance": cache_stats,
            "batch_performance": batch_stats,
            "overall_health": _calculate_health_score(
                query_stats, cache_stats, batch_stats
            )
        }
    
    except Exception as e:
        logger.error(f"Get performance summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Helper Functions =====

def _calculate_health_score(
    query_stats: Dict,
    cache_stats: Dict,
    batch_stats: Dict
) -> Dict:
    """Calculate overall performance health score"""
    
    # Query health (0-100)
    slow_query_rate = query_stats.get('slow_query_rate', 0)
    query_health = max(0, 100 - (slow_query_rate * 200))  # 50% slow = 0 health
    
    # Cache health (0-100)
    cache_hit_rate = cache_stats.get('hit_rate', 0)
    cache_health = cache_hit_rate * 100
    
    # Batch health (0-100)
    batch_error_rate = (
        batch_stats['errors'] / max(1, batch_stats['batches_processed'])
    )
    batch_health = max(0, 100 - (batch_error_rate * 200))
    
    # Overall (weighted average)
    overall = (query_health * 0.4 + cache_health * 0.4 + batch_health * 0.2)
    
    return {
        "overall_score": round(overall, 1),
        "query_health": round(query_health, 1),
        "cache_health": round(cache_health, 1),
        "batch_health": round(batch_health, 1),
        "status": (
            "excellent" if overall >= 90 else
            "good" if overall >= 70 else
            "fair" if overall >= 50 else
            "poor"
        )
    }
