"""
Graph Links Ingestor
- Reads cross-chain links from bridge/mixer heuristics
- Persists links into Neo4j using neo4j_client
"""
from __future__ import annotations
import asyncio
import os
from typing import Dict, Any, List
from datetime import datetime

from app.normalizer.bridge_patterns import get_cross_chain_links
from app.db.neo4j_client import neo4j_client


async def ingest_cross_chain_links(links: List[Dict[str, Any]]) -> int:
    """Persist provided cross-chain links into Neo4j.
    Returns number of links attempted.
    """
    # We only persist BRIDGE_LINK relations for now; MIXER_LINK can be added similarly
    count = 0
    now_iso = datetime.utcnow().isoformat()

    for link in links:
        rel = link.get("relationship")
        if rel == "BRIDGE_LINK":
            props = link.get("properties", {})
            # We do not have concrete addresses here (heuristics), so we store chain-to-chain link between pseudo nodes
            from_chain = (link.get("from_chain") or "").lower()
            to_chain = (link.get("to_chain") or "").lower()
            bridge_name = link.get("bridge_name") or props.get("bridge_name") or "unknown"

            # Use synthetic addresses to represent chain endpoints (namespaced)
            from_addr = f"chain:{from_chain}:bridge:{bridge_name}"
            to_addr = f"chain:{to_chain}:bridge:{bridge_name}"

            try:
                await neo4j_client.create_bridge_link(
                    from_address=from_addr,
                    to_address=to_addr,
                    bridge=bridge_name,
                    chain_from=from_chain,
                    chain_to=to_chain,
                    tx_hash=props.get("contract_address", "synthetic"),
                    timestamp_iso=now_iso,
                )
                count += 1
            except Exception:
                # Best-effort; continue
                pass
        # Future: handle MIXER_LINK similarly with dedicated relationship type
    return count


async def run_once() -> Dict[str, Any]:
    """Load cross-chain links and ingest them into Neo4j"""
    # Ensure TEST_MODE default if not explicitly configured to avoid real DB in local runs
    os.environ.setdefault("TEST_MODE", "1")

    links = get_cross_chain_links()
    total = len(links)
    persisted = await ingest_cross_chain_links(links)
    return {"links_total": total, "links_persisted": persisted}


if __name__ == "__main__":
    print(asyncio.run(run_once()))
