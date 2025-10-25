from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
import time
import asyncio
from datetime import datetime

from app.db.postgres import postgres_client
from app.db.neo4j_client import neo4j_client
from app.utils.jsonrpc import _get_redis  # reuse internal getter
from app.observability.metrics import POSTGRES_UP, REDIS_UP, EVIDENCE_VAULT_UP
from app.config import settings

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthz", summary="Liveness/Readiness probe")
async def healthz() -> Dict[str, Any]:
    """
    Lightweight liveness endpoint. Must not fail when dependencies are missing.
    - In TEST_MODE or when clients are not initialized, skip deep checks.
    - Always return a 200 with ok:true for simple availability probes.
    """
    status: Dict[str, Any] = {"ok": True, "services": {}}

    # Short-circuit in test/headless environments
    try:
        import os
        if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
            status["services"] = {
                "postgres": {"up": None},
                "neo4j": {"up": None},
                "redis": {"up": None},
            }
            return status
    except Exception:
        # Fall through to best-effort checks
        pass

    # Postgres (best-effort; skip if pool not initialized)
    pg_up: Optional[bool] = None
    try:
        if getattr(postgres_client, "pool", None) is not None:
            async with postgres_client.acquire() as conn:
                await conn.execute("SELECT 1")
            pg_up = True
        else:
            pg_up = None
    except Exception:
        pg_up = False
    try:
        if pg_up is True:
            POSTGRES_UP.set(1)
        elif pg_up is False:
            POSTGRES_UP.set(0)
    except Exception:
        pass
    status["services"]["postgres"] = {"up": pg_up}
    if pg_up is False:
        status["ok"] = False

    # Neo4j (best-effort; skip if client missing)
    neo_up: Optional[bool] = None
    try:
        if neo4j_client is not None:
            await neo4j_client.verify_connectivity()
            neo_up = True
        else:
            neo_up = None
    except Exception:
        neo_up = False
    status["services"]["neo4j"] = {"up": neo_up}
    if neo_up is False:
        status["ok"] = False

    # Redis (best-effort; treat not configured as None)
    red_up: Optional[bool] = None
    try:
        client = await _get_redis()
        if client is not None:
            try:
                await client.ping()
                red_up = True
            except Exception:
                red_up = False
        else:
            red_up = None
        if red_up is True:
            REDIS_UP.set(1)
        elif red_up is False:
            REDIS_UP.set(0)
    except Exception:
        red_up = False
    status["services"]["redis"] = {"up": red_up}
    if red_up is False:
        status["ok"] = False

    return status


@router.get("/health/detailed", summary="Detailed Health Check with Latency")
async def health_detailed() -> Dict[str, Any]:
    """
    Umfassender Health Check mit Latenz-Messungen für alle Services.
    
    Returns:
    - status: overall (healthy/degraded/unhealthy)
    - services: dict mit detaillierten Service-Infos
    - version: App-Version
    - timestamp: aktueller Zeitstempel
    - uptime: wie lange läuft die App (approximiert)
    """
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": settings.ENVIRONMENT,
        "services": {},
        "checks_duration_ms": 0
    }
    
    degraded_services: List[str] = []
    failed_services: List[str] = []
    
    # 1. PostgreSQL Check
    pg_result = await _check_postgres()
    health_status["services"]["postgres"] = pg_result
    if not pg_result["healthy"]:
        failed_services.append("postgres")
    elif pg_result.get("latency_ms", 0) > 100:
        degraded_services.append("postgres")
    
    # 2. Neo4j Check
    neo_result = await _check_neo4j()
    health_status["services"]["neo4j"] = neo_result
    if not neo_result["healthy"]:
        failed_services.append("neo4j")
    elif neo_result.get("latency_ms", 0) > 200:
        degraded_services.append("neo4j")
    
    # 3. Redis Check
    redis_result = await _check_redis()
    health_status["services"]["redis"] = redis_result
    if not redis_result["healthy"]:
        # Redis ist optional, daher nur degraded
        degraded_services.append("redis")
    
    # 4. Qdrant Check (wenn konfiguriert)
    qdrant_result = await _check_qdrant()
    if qdrant_result:
        health_status["services"]["qdrant"] = qdrant_result
        if not qdrant_result["healthy"]:
            degraded_services.append("qdrant")
    
    # 5. Kafka Check (wenn konfiguriert)
    kafka_result = await _check_kafka()
    if kafka_result:
        health_status["services"]["kafka"] = kafka_result
        if not kafka_result["healthy"]:
            degraded_services.append("kafka")
    
    # 6. Evidence Vault Check
    ev_result = await _check_evidence_vault()
    health_status["services"]["evidence_vault"] = ev_result
    if not ev_result["healthy"]:
        degraded_services.append("evidence_vault")

    # 7. Blockchain RPC Check
    rpc_result = await _check_blockchain_rpc()
    if rpc_result:
        health_status["services"]["blockchain_rpc"] = rpc_result
        if not rpc_result["healthy"]:
            degraded_services.append("blockchain_rpc")
    
    # 8. Solana RPC Check (wenn konfiguriert)
    sol_result = await _check_solana()
    if sol_result:
        health_status["services"]["solana"] = sol_result
        if not sol_result["healthy"]:
            degraded_services.append("solana")
    
    # 8. Config: DEX Routers EVM vorhanden?
    try:
        routers = getattr(settings, 'DEX_ROUTERS_EVM', []) or []
        if len(routers) == 0:
            health_status["services"]["dex_routers_evm"] = {
                "healthy": False,
                "configured": False,
                "warning": "DEX_ROUTERS_EVM is empty; dex_swap heuristics inactive"
            }
            degraded_services.append("dex_routers_evm")
        else:
            health_status["services"]["dex_routers_evm"] = {
                "healthy": True,
                "configured": True,
                "count": len(routers)
            }
    except Exception:
        pass
    
    # Overall Status
    if failed_services:
        health_status["status"] = "unhealthy"
        health_status["failed_services"] = failed_services
    elif degraded_services:
        health_status["status"] = "degraded"
        health_status["degraded_services"] = degraded_services
    
    health_status["checks_duration_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return health_status


@router.get("/health/ready", summary="Readiness Probe (Kubernetes)")
async def health_ready() -> Dict[str, Any]:
    """
    Readiness probe für Kubernetes.
    Gibt 200 zurück wenn App bereit ist, Traffic zu empfangen.
    Gibt 503 zurück wenn kritische Services fehlen.
    """
    # Kritische Services: Postgres, Neo4j
    critical_checks = []
    
    # Postgres
    try:
        async with postgres_client.acquire() as conn:
            await asyncio.wait_for(conn.execute("SELECT 1"), timeout=2.0)
        critical_checks.append({"postgres": True})
    except Exception as e:
        logger.error(f"Readiness check failed for Postgres: {e}")
        raise HTTPException(status_code=503, detail="Postgres not ready")
    
    # Neo4j
    try:
        await asyncio.wait_for(neo4j_client.verify_connectivity(), timeout=2.0)
        critical_checks.append({"neo4j": True})
    except Exception as e:
        logger.error(f"Readiness check failed for Neo4j: {e}")
        raise HTTPException(status_code=503, detail="Neo4j not ready")
    
    return {"ready": True, "checks": critical_checks}


@router.get("/health/live", summary="Liveness Probe (Kubernetes)")
async def health_live() -> Dict[str, Any]:
    """
    Liveness probe für Kubernetes.
    Gibt immer 200 zurück wenn die App läuft (kein Deadlock).
    """
    return {"alive": True, "timestamp": time.time()}


# ========== Helper Functions ==========

async def _check_postgres() -> Dict[str, Any]:
    """Prüft PostgreSQL mit Latenz-Messung"""
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None
    }
    
    try:
        async with postgres_client.acquire() as conn:
            await conn.execute("SELECT 1")
            # Prüfe auch Tabellen-Zugriff
            row = await conn.fetchrow("SELECT COUNT(*) FROM users LIMIT 1")
            result["healthy"] = True
            result["users_count"] = row[0] if row else 0
        POSTGRES_UP.set(1)
    except Exception as e:
        result["error"] = str(e)
        POSTGRES_UP.set(0)
        logger.warning(f"Postgres health check failed: {e}")
    
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_solana() -> Optional[Dict[str, Any]]:
    """Prüft Solana RPC (optional)"""
    if not hasattr(settings, 'SOLANA_RPC_URL') or not settings.SOLANA_RPC_URL:
        return None
    start = time.time()
    result: Dict[str, Any] = {
        "healthy": False,
        "latency_ms": 0,
        "error": None,
        "chain": "solana"
    }
    try:
        from app.adapters.solana_adapter import SolanaAdapter
        adapter = SolanaAdapter(getattr(settings, 'SOLANA_RPC_URL', None))
        h = await adapter.health()
        result["healthy"] = bool(h.get("rpc")) and h.get("status") in {"ready", "beta"}
        if "slot" in h:
            result["slot"] = h["slot"]
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Solana health check failed: {e}")
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_neo4j() -> Dict[str, Any]:
    """Prüft Neo4j mit Latenz-Messung und Node-Count"""
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None
    }
    
    try:
        await neo4j_client.verify_connectivity()
        # Zähle Nodes
        query = "MATCH (n) RETURN count(n) as count LIMIT 1"
        records = await neo4j_client.execute_query(query)
        if records:
            result["node_count"] = records[0]["count"]
        result["healthy"] = True
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Neo4j health check failed: {e}")
    
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_redis() -> Dict[str, Any]:
    """Prüft Redis mit Latenz-Messung"""
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None,
        "configured": False
    }
    
    client = await _get_redis()
    if client is None:
        result["error"] = "Redis not configured"
        return result
    
    result["configured"] = True
    
    try:
        await client.ping()
        # Teste SET/GET
        test_key = "health_check:test"
        await client.set(test_key, "ok", ex=60)
        val = await client.get(test_key)
        result["healthy"] = (val == "ok")
        REDIS_UP.set(1)
    except Exception as e:
        result["error"] = str(e)
        REDIS_UP.set(0)
        logger.warning(f"Redis health check failed: {e}")
    
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_qdrant() -> Optional[Dict[str, Any]]:
    """Prüft Qdrant Vector Database"""
    if not hasattr(settings, 'QDRANT_URL') or not settings.QDRANT_URL:
        return None
    
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None
    }
    
    try:
        from app.db.qdrant_client import qdrant_client
        # Teste Collection-Listing
        collections = await qdrant_client.list_collections()
        result["healthy"] = True
        result["collections_count"] = len(collections) if collections else 0
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Qdrant health check failed: {e}")
    
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_kafka() -> Optional[Dict[str, Any]]:
    """Prüft Kafka Connection"""
    if not hasattr(settings, 'KAFKA_BOOTSTRAP_SERVERS'):
        return None
    
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None,
        "configured": True,
    }
    try:
        servers = str(getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '')).split(',')
        target = servers[0].strip() if servers and servers[0] else ''
        # Strip optional scheme
        if '://' in target:
            target = target.split('://', 1)[1]
        host = target
        port = 9092
        if ':' in target:
            host, p = target.rsplit(':', 1)
            try:
                port = int(p)
            except ValueError:
                port = 9092

        # Async TCP connect with timeout
        try:
            await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2.0)
            result["healthy"] = True
        except Exception as e:
            result["error"] = f"TCP connect failed to {host}:{port} - {e}"
    except Exception as e:
        result["error"] = str(e)
    finally:
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_blockchain_rpc() -> Optional[Dict[str, Any]]:
    """Prüft Blockchain RPC (z.B. Ethereum)"""
    if not hasattr(settings, 'ETHEREUM_RPC_URL') or not settings.ETHEREUM_RPC_URL:
        return None
    
    start = time.time()
    result = {
        "healthy": False,
        "latency_ms": 0,
        "error": None,
        "chain": "ethereum"
    }
    
    try:
        from app.adapters.web3_client import web3_client
        # Teste Block-Number
        block_num = await web3_client.get_block_number()
        result["healthy"] = block_num > 0
        result["latest_block"] = block_num
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Blockchain RPC health check failed: {e}")
    
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result


async def _check_evidence_vault() -> Dict[str, Any]:
    """Prüft Evidence Vault (Append-only Log)"""
    start = time.time()
    result: Dict[str, Any] = {
        "healthy": False,
        "latency_ms": 0,
        "error": None,
        "has_head": False,
    }
    try:
        from app.services.evidence_vault import evidence_vault
        # Best-effort: funktioniert auch mit File-Fallback
        head = await evidence_vault.head()
        result["healthy"] = True
        result["has_head"] = bool(head)
        try:
            EVIDENCE_VAULT_UP.set(1)
        except Exception:
            pass
    except Exception as e:
        result["error"] = str(e)
        try:
            EVIDENCE_VAULT_UP.set(0)
        except Exception:
            pass
    result["latency_ms"] = round((time.time() - start) * 1000, 2)
    return result
