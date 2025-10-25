"""
Offline Indexer mit Adapter-Hooks
==================================

Erweitert um:
- Hooks in BitcoinAdapter.transform_transaction
- Hooks in EthereumAdapter.get_transaction
- Sammelt TX/Block-Daten in offline_* Tabellen
- Background-Job für historische Ingestion
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Importe verschieben (lazy)
postgres_client = None
_task: Optional[asyncio.Task] = None
_running = False


async def _get_postgres():
    """Lazy Postgres-Import"""
    global postgres_client
    if postgres_client is None:
        try:
            from app.db.postgres_client import postgres_client as pc
            postgres_client = pc
        except Exception as e:
            logger.warning(f"OfflineIndexer: Postgres unavailable: {e}")
    return postgres_client


async def hook_bitcoin_transaction(event: Dict[str, Any]) -> None:
    """Hook für BitcoinAdapter.transform_transaction - sammelt TX in offline_transactions"""
    if not await _should_index():
        return

    pc = await _get_postgres()
    if not pc:
        return

    try:
        async with pc.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO offline_transactions (chain, tx_hash, block_number, ts, from_address, to_address, value)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (chain, tx_hash) DO NOTHING
                """,
                "bitcoin",
                event.get("tx_hash"),
                event.get("block_number"),
                event.get("block_timestamp"),
                event.get("from_address"),
                event.get("to_address"),
                event.get("value")
            )
    except Exception as e:
        logger.warning(f"OfflineIndexer Bitcoin hook failed: {e}")


async def hook_ethereum_transaction(tx: Dict[str, Any]) -> None:
    """Hook für EthereumAdapter.get_transaction - sammelt TX in offline_transactions"""
    if not await _should_index():
        return

    pc = await _get_postgres()
    if not pc:
        return

    try:
        async with pc.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO offline_transactions (chain, tx_hash, block_number, ts, from_address, to_address, value, risk_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (chain, tx_hash) DO NOTHING
                """,
                "ethereum",
                tx.get("tx_hash") or tx.get("hash"),
                tx.get("block_number"),
                tx.get("timestamp"),
                tx.get("from_address") or tx.get("from"),
                tx.get("to_address") or tx.get("to"),
                tx.get("value"),
                tx.get("risk_score", 0.0)
            )
    except Exception as e:
        logger.warning(f"OfflineIndexer Ethereum hook failed: {e}")


async def hook_block(chain: str, block_number: int, block_hash: str, ts: datetime) -> None:
    """Hook für Block-Daten - sammelt in offline_blocks"""
    if not await _should_index():
        return

    pc = await _get_postgres()
    if not pc:
        return

    try:
        async with pc.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO offline_blocks (chain, number, hash, ts)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (chain, number) DO NOTHING
                """,
                chain, block_number, block_hash, ts
            )
    except Exception as e:
        logger.warning(f"OfflineIndexer Block hook failed: {e}")


async def _should_index() -> bool:
    """Prüft, ob Indexing aktiviert ist und Postgres verfügbar"""
    return (
        os.getenv("ENABLE_OFFLINE_INDEX", "0") == "1" and
        os.getenv("TEST_MODE") != "1"
    )


async def _run_historical_ingestion(chain: str = "ethereum", start_block: int = 0, max_blocks: int = 100) -> int:
    """Historische Ingestion: Sammelt TXs von start_block für max_blocks"""
    pc = await _get_postgres()
    if not pc:
        return 0

    try:
        # Mock: Sammelt aus bestehenden TX-Tabellen (in Produktion: RPC-Adapter)
        async with pc.acquire() as conn:
            # Beispiel: Kopiere aus transactions-Tabelle
            rows = await conn.fetch(
                """
                SELECT tx_hash, block_number, timestamp, from_address, to_address, value
                FROM transactions
                WHERE chain = $1 AND block_number >= $2
                ORDER BY block_number ASC
                LIMIT $3
                """,
                chain, start_block, max_blocks
            )

            for row in rows:
                await conn.execute(
                    """
                    INSERT INTO offline_transactions (chain, tx_hash, block_number, ts, from_address, to_address, value)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (chain, tx_hash) DO NOTHING
                    """,
                    chain, row["tx_hash"], row["block_number"], row["timestamp"],
                    row["from_address"], row["to_address"], row["value"]
                )

        return len(rows)
    except Exception as e:
        logger.warning(f"Historical ingestion failed for {chain}: {e}")
        return 0


# Background-Job bleibt wie zuvor, aber mit erweiterter Ingestion
async def _run_loop(interval: int, per_run: int) -> None:
    global _running
    _running = True
    try:
        while _running:
            try:
                # Erweitert: Historische Ingestion für mehrere Chains
                chains = ["ethereum", "bitcoin"]
                for chain in chains:
                    indexed = await _run_historical_ingestion(chain, max_blocks=per_run)
                    logger.info(f"OfflineIndexer: indexed {indexed} historical TXs for {chain}")
            except Exception as e:
                logger.warning(f"OfflineIndexer: iteration failed: {e}")
            await asyncio.sleep(interval)
    except Exception as e:
        logger.error(f"OfflineIndexer: loop error: {e}")
    finally:
        _running = False


# Start/Stop bleiben gleich
def start_offline_indexer(interval_seconds: Optional[int] = None, max_per_run: Optional[int] = None) -> Optional[asyncio.Task]:
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
    global _running, _task
    _running = False
    if _task and not _task.done():
        try:
            _task.cancel()
        except Exception:
            pass
    logger.info("🛑 OfflineIndexer stopped")
