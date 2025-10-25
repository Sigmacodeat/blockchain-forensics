"""
System API - Monitoring and Health
"""

import logging
import time
import psutil
import asyncio
import platform
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_strict, get_current_user_optional
from app.db.postgres import postgres_client
from app.db.redis_client import redis_client
from app.services.alert_service import alert_service
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)
router = APIRouter()


class SystemHealthResponse(BaseModel):
    """System health response"""
    status: str
    timestamp: str
    uptime: float
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    database: Dict[str, Any]
    workers: Dict[str, Any]
    services: Dict[str, Any]


class WorkerStatusResponse(BaseModel):
    """Worker status response"""
    name: str
    status: str  # running, stopped, error
    last_heartbeat: Optional[str]
    processed_count: int
    error_count: int
    uptime_seconds: float


@router.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """Liveness probe: leichtgewichtiger Prozess-/Loop-Check."""
    try:
        # Event loop sanity
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("event loop closed")
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": time.time() - psutil.boot_time(),
            "platform": platform.platform(),
        }
    except Exception as e:
        logger.error(f"healthz failed: {e}")
        raise HTTPException(status_code=500, detail="liveness failed")


@router.get("/readyz")
async def readyz() -> Dict[str, Any]:
    """Readiness probe: tiefer Check inkl. Datenbank und Kernservices."""
    try:
        # DB check
        db_healthy = await postgres_client.health_check()
        # Redis check
        try:
            redis_healthy = await redis_client.verify_connectivity()
        except Exception:
            redis_healthy = False
        # Alert engine readiness via service facade
        engine_ready = alert_service.is_engine_ready()
        alerts_cached = alert_service.cached_alerts_count() if engine_ready else 0
        # At least one worker heartbeat present?
        try:
            hb_map = await redis_client.list_worker_statuses()
            workers_ready = any((v.get("status") in ("running", "ok")) for v in hb_map.values())
            workers_count = len(hb_map)
        except Exception:
            workers_ready = False
            workers_count = 0

        ready = bool(db_healthy) and bool(redis_healthy) and bool(engine_ready)
        status = "ready" if ready else "not_ready"
        return {
            "status": status,
            "database": {"healthy": bool(db_healthy)},
            "redis": {"healthy": bool(redis_healthy)},
            "alert_engine": {"ready": bool(engine_ready), "alerts_cached": alerts_cached},
            "workers": {"ready": bool(workers_ready), "count": workers_count},
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"readyz failed: {e}")
        raise HTTPException(status_code=500, detail="readiness failed")


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(current_user: dict | None = Depends(get_current_user_optional)) -> SystemHealthResponse:
    """Get comprehensive system health status"""
    try:
        # System metrics
        uptime_seconds = time.time() - psutil.boot_time()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Database health
        db_health = await postgres_client.health_check()
        db_stats = postgres_client.get_connection_stats()
        # best-effort response time extraction
        try:
            db_response_time = float(db_stats.get("avg_query_time_ms") or db_stats.get("response_time_ms") or 0.0)
        except Exception:
            db_response_time = 0.0

        # Worker status via Redis heartbeats (real data, dynamic discovery)
        workers: Dict[str, Any] = {}
        try:
            hb_map = await redis_client.list_worker_statuses()
            for wname, hb in hb_map.items():
                workers[wname] = {
                    "status": hb.get("status", "unknown"),
                    "processed": int(hb.get("processed_count", 0)),
                    "errors": int(hb.get("error_count", 0)),
                    "last_heartbeat": hb.get("last_heartbeat"),
                }
        except Exception:
            pass
        # Ensure known workers are represented even if no heartbeat yet
        for wname in ("monitor_worker", "threat_intel_worker"):
            if wname not in workers:
                workers[wname] = {
                    "status": "not_running",
                    "processed": 0,
                    "errors": 0,
                    "last_heartbeat": None,
                }

        # Services status
        any_not_running = any(v.get("status") not in ("running", "ok") for v in workers.values())
        # alert engine readiness (boolean expected by FE)
        try:
            engine_ready = alert_service.is_engine_ready()
        except Exception:
            engine_ready = False
        # graph db ping (best-effort)
        graph_ok = False
        try:
            from app.db.neo4j_client import neo4j_client  # local import to avoid heavy dep if not configured
            async with neo4j_client.get_session() as session:
                await session.run("RETURN 1 as ok")
                graph_ok = True
        except Exception:
            graph_ok = False
        # ml service availability (heuristic)
        ml_ok = False
        try:
            from app.services.ml_model_service import ml_model_service  # type: ignore
            ml_ok = bool(ml_model_service is not None)
        except Exception:
            ml_ok = False

        services = {
            # detailed objects
            "api": {"status": "healthy", "uptime": time.time() - psutil.boot_time()},
            "database": {"status": "healthy" if db_health else "unhealthy", "stats": db_stats},
            "workers": {"status": "running" if not any_not_running else "degraded", "count": len(workers)},
            # booleans expected by FE cards
            "alert_engine": engine_ready,
            "graph_db": graph_ok,
            "ml_service": ml_ok,
        }

        # Build database section with FE-compatible keys
        database_section = {
            "healthy": db_health,
            "connected": bool(db_health),
            "response_time": db_response_time,
            "stats": db_stats,
        }

        # Compose response
        resp = SystemHealthResponse(
            status="healthy" if db_health else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            uptime=uptime_seconds,
            uptime_seconds=uptime_seconds,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            database=database_section,
            workers=workers,
            services=services,
        )
        return resp
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/system/workers", response_model=Dict[str, WorkerStatusResponse])
async def get_worker_status(current_user: dict = Depends(get_current_user_strict)) -> Dict[str, WorkerStatusResponse]:
    """Get worker process status"""
    try:
        workers: Dict[str, WorkerStatusResponse] = {}
        try:
            hb_map = await redis_client.list_worker_statuses()
        except Exception:
            hb_map = {}

        # Include any discovered workers
        for wname, hb in hb_map.items():
            workers[wname] = WorkerStatusResponse(
                name=wname,
                status=str(hb.get("status", "unknown")),
                last_heartbeat=str(hb.get("last_heartbeat")),
                processed_count=int(hb.get("processed_count", 0)),
                error_count=int(hb.get("error_count", 0)),
                uptime_seconds=float(time.time() - psutil.boot_time()),
            )

        # Ensure known workers are present
        for wname in ("monitor_worker", "threat_intel_worker"):
            if wname not in workers:
                workers[wname] = WorkerStatusResponse(
                    name=wname,
                    status="not_running",
                    last_heartbeat=None,
                    processed_count=0,
                    error_count=0,
                    uptime_seconds=float(time.time() - psutil.boot_time()),
                )

        return workers
    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(status_code=500, detail="Worker status check failed")


@router.get("/system/metrics")
async def get_system_metrics(current_user: dict = Depends(get_current_user_strict)):
    """Get detailed system metrics"""
    try:
        # Process information
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_times = process.cpu_times()

        # Network connections
        connections = len(process.connections())

        # Open files (limit to avoid performance issues)
        try:
            open_files = len(process.open_files()[:100])  # Sample
        except Exception:
            open_files = 0

        return {
            "process": {
                "pid": process.pid,
                "memory_rss_mb": memory_info.rss / 1024 / 1024,
                "memory_vms_mb": memory_info.vms / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "cpu_times_user": cpu_times.user,
                "cpu_times_system": cpu_times.system,
                "threads": process.num_threads(),
                "connections": connections,
                "open_files": open_files,
            },
            "system": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "memory_available_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Metrics collection failed")


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus scrape endpoint (unauthenticated)."""
    try:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        # Return 500 if metrics generation fails
        raise HTTPException(status_code=500, detail="metrics generation failed")
