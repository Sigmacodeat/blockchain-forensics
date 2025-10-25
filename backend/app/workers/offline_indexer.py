"""
Offline Indexer (optional)
==========================

Indexiert Blockchain-Daten in eine lokale Postgres-Speicherstruktur für Offline-Analysen.

Aktivierung über ENV: ENABLE_OFFLINE_INDEX=1
Konfiguration:
- OFFLINE_INDEX_INTERVAL_SECONDS (Default 900)
- OFFLINE_INDEX_MAX_PER_RUN (Default 200)

Sicherheitsprinzipien:
- No-Op in TEST_MODE oder wenn Postgres/Adapter nicht verfügbar sind
- Best-effort Logging, keine Exceptions nach außen
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None
_running = False


async def _ensure_tables(conn) -> None:
    # Minimale Tabellen für Offline-Index
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_blocks (
            id BIGSERIAL PRIMARY KEY,
            chain VARCHAR(32) NOT NULL,
            number BIGINT NOT NULL,
            hash TEXT,
            ts TIMESTAMPTZ,
            indexed_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(chain, number)
        )
        """
    )
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_transactions (
            id BIGSERIAL PRIMARY KEY,
            chain VARCHAR(32) NOT NULL,
            tx_hash TEXT NOT NULL,
            block_number BIGINT,
            ts TIMESTAMPTZ,
            from_address TEXT,
            to_address TEXT,
            value DOUBLE PRECISION,
            risk_score DOUBLE PRECISION,
            indexed_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(chain, tx_hash)
        )
        """
    )


async def _index_evm_latest(conn, max_items: int = 200) -> int:
    # Platzhalter: sammelt keine externen RPCs im MVP, reserviert Schnittstelle
    # Erweiterung: Nutzung eines EVM-Adapters, wenn konfiguriert.
    return 0


async def _index_utxo_latest(conn, max_items: int = 200) -> int:
    # Platzhalter: sammelt keine externen RPCs im MVP
    return 0


async def _run_loop(interval: int, per_run: int) -> None:
    global _running
    _running = True
    try:
        from app.db.postgres_client import postgres_client
    except Exception as e:
        logger.warning(f"OfflineIndexer: postgres client unavailable: {e}")
        _running = False
        return

    while _running:
        try:
            if os.getenv("TEST_MODE") == "1":
                logger.info("OfflineIndexer: TEST_MODE -> sleeping")
                await asyncio.sleep(interval)
                continue

            async with postgres_client.acquire() as conn:
                await _ensure_tables(conn)
                evm_cnt = await _index_evm_latest(conn, per_run)
                utxo_cnt = await _index_utxo_latest(conn, per_run)
                logger.info(f"OfflineIndexer: indexed evm={evm_cnt} utxo={utxo_cnt}")
        except Exception as e:
            logger.warning(f"OfflineIndexer: iteration failed: {e}")
        await asyncio.sleep(interval)


def start_offline_indexer(interval_seconds: Optional[int] = None, max_per_run: Optional[int] = None) -> Optional[asyncio.Task]:
    """Startet den Offline-Indexer als Background-Task, wenn aktiviert."""
    if os.getenv("ENABLE_OFFLINE_INDEX", "0") != "1":
        logger.info("OfflineIndexer: disabled (ENABLE_OFFLINE_INDEX!=1)")
        return None
    if os.getenv("TEST_MODE") == "1":
        logger.info("OfflineIndexer: disabled in TEST_MODE")
        return None

    interval = interval_seconds or int(os.getenv("OFFLINE_INDEX_INTERVAL_SECONDS", "900"))
    per_run = max_per_run or int(os.getenv("OFFLINE_INDEX_MAX_PER_RUN", "200"))

    global _task
    if _task and not _task.done():
        return _task
    loop = asyncio.get_event_loop()
    _task = loop.create_task(_run_loop(interval, per_run))
    logger.info(f"✅ OfflineIndexer started (interval={interval}s, per_run={per_run})")
    return _task


def stop_offline_indexer() -> None:
    """Stoppt den Offline-Indexer-Task (best-effort)."""
    global _running, _task
    _running = False
    if _task and not _task.done():
        try:
            _task.cancel()
        except Exception:
            pass
    logger.info("🛑 OfflineIndexer stopped")
