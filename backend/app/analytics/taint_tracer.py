"""
Lightweight Taint Tracer (v1)
- ABI-lose, chain-agnostische Heuristiken (EVM/UTXO kompatible Felder)
- Nutzt MultiChainForensics APIs, keine direkten RPC-Annahmen
- Fokus: schnelle Erstanalyse (Forward-Trace) bis max_hops
"""
from __future__ import annotations
from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from app.services.multi_chain import multi_chain_engine


@dataclass
class TaintEdge:
    chain: str
    tx_hash: Optional[str]
    from_address: Optional[str]
    to_address: Optional[str]
    amount: Optional[int]
    block_number: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain": self.chain,
            "tx_hash": self.tx_hash,
            "from": self.from_address,
            "to": self.to_address,
            "amount": self.amount,
            "block_number": self.block_number,
        }


@dataclass
class TaintResult:
    seed: str
    hops: int
    edges: List[TaintEdge]
    visited: Set[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "hops": self.hops,
            "edges": [e.to_dict() for e in self.edges],
            "visited": list(self.visited),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }


async def _fetch_neighbors(chain_id: str, address: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Holt grob relevante Transaktionen für eine Adresse.
    Nutzt get_address_transactions_paged (Fallback, wenn keine Blockgrenzen angegeben sind).
    """
    try:
        items = await multi_chain_engine.get_address_transactions_paged(chain_id, address, limit=limit)
        return items or []
    except Exception:
        return []


def _edge_from_tx(chain_id: str, addr: str, tx: Dict[str, Any]) -> Optional[TaintEdge]:
    """Heuristik zur Extraktion einer gerichteten Kante aus einer TX abhängig von Feldern.
    Erwartete generische Felder: from, to, value, hash, blockNumber (EVM-ähnlich).
    """
    frm = (tx.get("from") or tx.get("sender") or "").lower() if isinstance(tx.get("from") or tx.get("sender"), str) else None
    to = (tx.get("to") or tx.get("receiver") or "").lower() if isinstance(tx.get("to") or tx.get("receiver"), str) else None
    val = None
    v = tx.get("value") or tx.get("amount")
    try:
        if isinstance(v, str) and v.startswith("0x"):
            val = int(v, 16)
        elif isinstance(v, (int, float)):
            val = int(v)
    except Exception:
        val = None
    hsh = tx.get("hash") or tx.get("tx_hash")
    blk = None
    try:
        b = tx.get("blockNumber") or tx.get("block_number")
        if isinstance(b, str) and b.startswith("0x"):
            blk = int(b, 16)
        elif isinstance(b, int):
            blk = b
    except Exception:
        blk = None

    if frm is None and to is None:
        return None

    # Richtung: falls seed = addr, dann outgoing (addr->counterparty), sonst incoming
    # Für generische Trace genügt die tatsächliche TX-Richtung
    return TaintEdge(
        chain=chain_id,
        tx_hash=hsh,
        from_address=frm,
        to_address=to,
        amount=val,
        block_number=blk,
    )


async def trace_forward(seed: str, chains: List[str], max_hops: int = 3, per_hop_limit: int = 50) -> TaintResult:
    """Forward-Trace ab einer Seed-Adresse über mehrere Chains.
    Einfache BFS über Nachbarn, ohne Duplikate, begrenzt durch max_hops.
    """
    seed_l = (seed or "").lower()
    edges: List[TaintEdge] = []
    visited: Set[str] = set([seed_l])
    frontier: List[Tuple[str, str]] = [(c, seed_l) for c in chains]

    for hop in range(1, max_hops + 1):
        next_frontier: List[Tuple[str, str]] = []
        tasks = [
            _fetch_neighbors(chain_id, addr, per_hop_limit)
            for chain_id, addr in frontier
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for (chain_id, addr), txs in zip(frontier, results):
            if not isinstance(txs, list):
                continue
            for tx in txs:
                e = _edge_from_tx(chain_id, addr, tx)
                if not e:
                    continue
                edges.append(e)
                # Füge neuen Knoten zur Frontier hinzu (Gegenpartei)
                neighbor = None
                if e.from_address == addr and e.to_address:
                    neighbor = e.to_address
                elif e.to_address == addr and e.from_address:
                    neighbor = e.from_address
                if neighbor and neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.append((chain_id, neighbor))
        frontier = next_frontier
        if not frontier:
            break

    return TaintResult(seed=seed_l, hops=hop if edges else 0, edges=edges, visited=visited)
