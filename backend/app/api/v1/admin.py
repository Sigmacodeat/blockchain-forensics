"""
Admin API
System Administration, Data Ingestion, Health Monitoring
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import BaseModel, Field

from app.ingest.blockchain_ingester import blockchain_ingester
from app.auth.dependencies import require_admin_strict, get_current_user_strict
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Request Models
class IngestAddressRequest(BaseModel):
    """Ingest address transactions"""
    address: str = Field(..., description="Ethereum address")
    start_block: int = Field(default=0, description="Start block number")
    limit: int = Field(default=100, ge=1, le=10000, description="Max transactions")


class IngestBlockRequest(BaseModel):
    """Ingest block transactions"""
    block_number: int = Field(..., ge=0, description="Block number")


class SystemStatsResponse(BaseModel):
    """System statistics"""
    total_transactions: int
    total_addresses: int
    total_traces: int
    database_size_mb: float
    cache_hit_rate: float


@router.post("/ingest/address")
async def ingest_address(
    request: IngestAddressRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin_strict),
):
    """
    Ingest transactions for an address

    **Background Task:**
    - Fetches from Ethereum RPC
    - Stores in TimescaleDB
    - Updates labels

    **Use Cases:**
    - Prepare address for tracing
    - Sync new transactions
    - Backfill historical data
    """
    try:
        logger.info(f"Starting ingestion for {request.address}")

        # Run in background
        background_tasks.add_task(
            blockchain_ingester.ingest_address_transactions,
            address=request.address,
            start_block=request.start_block,
            limit=request.limit
        )

        return {
            "status": "started",
            "address": request.address,
            "message": f"Ingestion started in background (limit: {request.limit})"
        }

    except Exception as e:
        logger.error(f"Error starting ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/block")
async def ingest_block(
    request: IngestBlockRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin_strict),
):
    """
    Ingest all transactions from a block

    **Use Cases:**
    - Sync specific blocks
    - Backfill missing data
    """
    try:
        logger.info(f"Starting block ingestion: {request.block_number}")

        background_tasks.add_task(
            blockchain_ingester.ingest_block,
            block_number=request.block_number
        )

        return {
            "status": "started",
            "block_number": request.block_number,
            "message": "Block ingestion started in background"
        }

    except Exception as e:
        logger.error(f"Error starting block ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats(current_user = Depends(require_admin_strict)):
    """
    Get system statistics

    **Metrics:**
    - Total transactions in DB
    - Total unique addresses
    - Total traces completed
    - Database size
    - Cache performance
    """
    try:
        from sqlalchemy import text
        from app.db.postgres_client import postgres_client
        from app.db.redis_client import redis_client
        from app.db.neo4j_client import neo4j_client

        total_transactions = 0
        total_addresses = 0
        database_size_mb = 0.0
        cache_hit_rate = 0.0
        total_traces = 0

        # Postgres metrics
        try:
            async with postgres_client.get_session() as session:
                # Transactions count
                r1 = await session.execute(text("SELECT COUNT(*) AS c FROM transactions"))
                total_transactions = int(r1.scalar() or 0)
                # Distinct addresses across from/to
                r2 = await session.execute(text(
                    """
                    SELECT COUNT(DISTINCT addr) AS c FROM (
                        SELECT from_address AS addr FROM transactions
                        UNION
                        SELECT to_address AS addr FROM transactions WHERE to_address IS NOT NULL
                    ) x
                    """
                ))
                total_addresses = int(r2.scalar() or 0)
                # Database size (MB)
                r3 = await session.execute(text("SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 AS mb"))
                database_size_mb = float(r3.scalar() or 0.0)
        except Exception as e:
            logger.warning(f"Stats: Postgres query failed: {e}")

        # Neo4j traces count
        try:
            async with neo4j_client.get_session() as nsession:
                res = await nsession.run("MATCH (t:Trace) RETURN count(t) AS c")
                rec = await res.single()
                total_traces = int(rec["c"] or 0)
        except Exception as e:
            logger.warning(f"Stats: Neo4j query failed: {e}")

        # Redis cache hit rate (best-effort)
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client is not None:
                info = await client.info(section="stats")  # type: ignore[attr-defined]
                hits = float(info.get("keyspace_hits", 0.0))
                misses = float(info.get("keyspace_misses", 0.0))
                denom = hits + misses
                cache_hit_rate = float(hits / denom) if denom > 0 else 0.0
        except Exception as e:
            logger.warning(f"Stats: Redis info failed: {e}")

        stats = SystemStatsResponse(
            total_transactions=total_transactions,
            total_addresses=total_addresses,
            total_traces=total_traces,
            database_size_mb=round(database_size_mb, 2),
            cache_hit_rate=round(cache_hit_rate, 4),
        )

        return stats

    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/db")
async def check_database_health(current_user = Depends(require_admin_strict)):
    """
    Check database connectivity

    **Checks:**
    - Neo4j connection
    - Postgres connection
    - Redis connection
    - Qdrant connection
    """
    try:
        from app.db.neo4j_client import neo4j_client
        from app.db.postgres_client import postgres_client
        from app.db.redis_client import redis_client
        from app.db.qdrant_client import qdrant_client

        health = {
            "neo4j": await neo4j_client.verify_connectivity(),
            "postgres": await postgres_client.verify_connectivity(),
            "redis": await redis_client.verify_connectivity(),
            "qdrant": qdrant_client.verify_connectivity()
        }

        all_healthy = all(health.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "databases": health
        }

    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.delete("/cache/clear")
async def clear_cache(current_user = Depends(require_admin_strict)):
    """
    Clear Redis cache

    **Warning:** This will clear all cached data!
    """
    try:
        from app.db.redis_client import redis_client
        deleted = await redis_client.clear_cache()
        return {"status": "success", "deleted": int(deleted)}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config(current_user = Depends(require_admin_strict)):
    """
    Get current configuration

    **Security:** Sensitive values are masked
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "max_trace_depth": settings.MAX_TRACE_DEPTH,
        "max_nodes_per_trace": settings.MAX_NODES_PER_TRACE,
        "taint_model": settings.TAINT_MODEL,
        "features": {
            "ml_clustering": settings.ENABLE_ML_CLUSTERING,
            "cross_chain": settings.ENABLE_CROSS_CHAIN,
            "ai_agents": settings.ENABLE_AI_AGENTS
        }
    }


@router.get("/users")
async def list_users(
    current_user = Depends(require_admin_strict),
):
    """
    List all users (Admin only)
    
    Returns basic user information for admin management
    """
    try:
        # Mock response for testing - in production, query actual users
        return {
            "users": [
                {
                    "id": "user-1",
                    "email": "test@example.com",
                    "plan": "pro",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "total": 1
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include chatbot config routes from admin package
try:
    from .admin.chatbot_config import router as chatbot_config_router
    router.include_router(chatbot_config_router, tags=["Chatbot Config"])
except Exception as e:
    logger.warning(f"Could not include chatbot config routes: {e}")

print("DEBUG: admin.py loaded, router has", len(router.routes), "routes")
