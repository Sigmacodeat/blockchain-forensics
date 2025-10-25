"""Bridge Hooks

Hilfsfunktionen zum sicheren Persistieren von Cross-Chain-Bridge-Links.
- TEST_MODE/OFFLINE_MODE-sicher (no-op)
- Normalisiert Adressen auf lower-case
"""
from __future__ import annotations

import os
from typing import Optional

from app.db.neo4j_client import neo4j_client


async def persist_bridge_link(
    from_address: str,
    to_address: str,
    *,
    bridge: str,
    chain_from: str,
    chain_to: str,
    tx_hash: str,
    timestamp_iso: str,
) -> bool:
    """Persistiert einen Bridge-Link. Gibt True bei Erfolg/No-Op zurück.

    No-Op, wenn TEST_MODE oder OFFLINE_MODE aktiv sind oder Neo4j nicht verbunden ist.
    """
    if os.getenv("TEST_MODE") == "1" or os.getenv("OFFLINE_MODE") == "1":
        return True
    try:
        await neo4j_client.create_bridge_link(
            from_address=from_address.lower(),
            to_address=to_address.lower(),
            bridge=bridge,
            chain_from=chain_from,
            chain_to=chain_to,
            tx_hash=tx_hash,
            timestamp_iso=timestamp_iso,
        )
        return True
    except Exception:
        return False
