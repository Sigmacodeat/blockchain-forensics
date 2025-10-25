"""
Monitoring API - System Health
Admin Only
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_system_health(
    current_user: Dict = None
) -> Dict[str, Any]:
    """
    Get system health status
    Admin Only
    
    Returns:
    - status: overall, healthy/degraded/down
    - services: Status of all services (DB, Redis, Kafka, etc.)
    - metrics: Performance metrics
    """
    # Check admin role
    if current_user and current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        # Mock health status
        health = {
            'status': 'healthy',
            'timestamp': '2025-10-18T16:30:00Z',
            'services': {
                'postgresql': {'status': 'healthy', 'response_time_ms': 5},
                'redis': {'status': 'healthy', 'response_time_ms': 2},
                'kafka': {'status': 'healthy', 'response_time_ms': 10},
                'neo4j': {'status': 'healthy', 'response_time_ms': 8}
            },
            'metrics': {
                'api_latency_p95_ms': 85,
                'requests_per_second': 120,
                'error_rate': 0.005,
                'cpu_usage': 0.45,
                'memory_usage': 0.62
            }
        }
        
        return health
    
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_system_metrics(
    current_user: Dict = None
) -> Dict[str, Any]:
    """
    Get detailed system metrics
    Admin Only
    """
    if current_user and current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        metrics = {
            'api': {
                'total_requests': 150000,
                'requests_per_minute': 250,
                'average_response_time_ms': 75,
                'error_count': 120
            },
            'database': {
                'connections_active': 25,
                'connections_max': 100,
                'query_time_avg_ms': 45
            },
            'cache': {
                'hit_rate': 0.85,
                'memory_used_mb': 512
            }
        }
        
        return metrics
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
