"""
Graph Service
Optional Neo4j-backed graph writer with safe no-op fallback.
"""
from __future__ import annotations

from typing import Any, Dict, List
import logging

try:
    from neo4j import GraphDatabase as _Neo4jGraphDatabase
    GraphDatabase: Any = _Neo4jGraphDatabase
except Exception:  # pragma: no cover
    GraphDatabase = None

from app.config import settings

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self):
        self.enabled = bool((GraphDatabase is not None) and getattr(settings, "NEO4J_URI", None))
        self._driver = None
        if self.enabled:
            try:
                self._driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
                logger.info("GraphService: Neo4j driver initialized")
            except Exception as e:  # pragma: no cover
                logger.warning(f"GraphService disabled (Neo4j init failed): {e}")
                self.enabled = False
        else:
            logger.info("GraphService: running in no-op mode")

    def close(self):
        if self._driver:
            self._driver.close()

    # --------------- public API ---------------
    def ingest_canonical(self, evt: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "noop"}
        q = """
        MERGE (t:Tx {hash:$tx_hash, chain:$chain})
          SET t.block=$block_number, t.type=$event_type, t.timestamp=$timestamp
        MERGE (a:Address {address:$from, chain:$chain})
        MERGE (b:Address {address:$to, chain:$chain})
        MERGE (a)-[r:SENT {tx:$tx_hash}]->(t)
          SET r.amount=$value
        MERGE (t)-[s:RECEIVED {tx:$tx_hash}]->(b)
          SET s.amount=$value
        RETURN t.hash as tx
        """
        params = {
            "tx_hash": evt.get("tx_hash"),
            "chain": evt.get("chain"),
            "block_number": evt.get("block_number"),
            "event_type": evt.get("event_type"),
            "timestamp": str(evt.get("timestamp")),
            "from": evt.get("from_address") or "",
            "to": evt.get("to_address") or "",
            "value": float(evt.get("value") or 0),
        }
        assert self._driver is not None
        with self._driver.session() as s:
            rec = s.run(q, **params).single()
            return {"tx": rec["tx"] if rec else evt.get("tx_hash")}

    def ingest_btc_edges(self, txid: str, edges: List[Dict[str, Any]], fee: float | None = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "noop"}
        q = """
        MERGE (t:Tx {hash:$txid, chain:'bitcoin'}) SET t.fee=$fee
        WITH t
        UNWIND $edges as e
        MERGE (prev:Tx {hash:e.from.txid, chain:'bitcoin'})
        MERGE (curr:Tx {hash:e.to.txid, chain:'bitcoin'})
        MERGE (prev)-[f:FLOWS {from_vout:e.from.vout, to_vout:e.to.vout}]->(curr)
          SET f.value = e.value
        RETURN count(f) as edges
        """
        params = {"txid": txid, "edges": edges, "fee": fee or 0.0}
        assert self._driver is not None
        with self._driver.session() as s:
            rec = s.run(q, **params).single()
            return {"edges": rec["edges"] if rec else 0}


service = GraphService()
