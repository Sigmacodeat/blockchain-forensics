"""
Wallet Clustering (v1)
- Heuristics:
  * Co-occurrence: Zwei Adressen in derselben Transaktion (gleicher tx_hash) -> gleicher Cluster-Kandidat
  * Counterparty linkage: Zwei Adressen teilen mindestens N gemeinsame Gegenparteien -> gleicher Cluster-Kandidat
- Datenquelle: multi_chain_engine.get_address_transactions_paged (chain-agnostisch)
- Ziel: Schnelle, erklärbare Vorschläge (keine DB-Persistenz)
"""
from __future__ import annotations
from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from app.services.multi_chain import multi_chain_engine


@dataclass
class ClusterSuggestion:
    members: List[str]
    score: float
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"members": self.members, "score": self.score, "reasons": self.reasons}


def _norm(addr: Optional[str]) -> Optional[str]:
    if isinstance(addr, str):
        s = addr.strip().lower()
        return s if s else None
    return None


def _extract_participants(tx: Dict[str, Any]) -> Set[str]:
    parts: Set[str] = set()
    for k in ("from", "to", "sender", "receiver"):
        v = _norm(tx.get(k))
        if v:
            parts.add(v)
    return parts


def _counterparties_for(address: str, txs: List[Dict[str, Any]]) -> Set[str]:
    cps: Set[str] = set()
    a = address
    for tx in txs:
        frm = _norm(tx.get("from") or tx.get("sender"))
        to = _norm(tx.get("to") or tx.get("receiver"))
        if frm == a and to:
            cps.add(to)
        elif to == a and frm:
            cps.add(frm)
    return cps


async def _fetch_all(chain_id: str, addresses: List[str], limit: int) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    tasks = [multi_chain_engine.get_address_transactions_paged(chain_id, addr, limit=limit) for addr in addresses]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for addr, res in zip(addresses, results):
        out[addr] = res if isinstance(res, list) else []
    return out


async def suggest_clusters(addresses: List[str], chains: List[str], limit_per_address: int = 100,
                           min_shared_counterparties: int = 3) -> Dict[str, Any]:
    """Liefert Cluster-Vorschläge und Begründungen.
    Output:
      { "clusters": [ {"members":[...], "score": float, "reasons": [..] } ], "analyzed": N }
    """
    addrs = sorted({_norm(a) for a in addresses if _norm(a)})
    if not addrs:
        return {"clusters": [], "analyzed": 0}

    # Daten holen pro Chain
    per_chain_data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for chain_id in chains:
        try:
            await multi_chain_engine.initialize_chains([chain_id])
            per_chain_data[chain_id] = await _fetch_all(chain_id, addrs, limit_per_address)
        except Exception:
            per_chain_data[chain_id] = {a: [] for a in addrs}

    # Heuristik 1: Co-occurrence im gleichen tx_hash
    tx_to_addrs: Dict[str, Set[str]] = defaultdict(set)
    for chain_id, addr_map in per_chain_data.items():
        for a, txs in addr_map.items():
            for tx in txs:
                h = tx.get("hash") or tx.get("tx_hash")
                if isinstance(h, str) and h:
                    parts = _extract_participants(tx)
                    if a in parts:
                        for p in parts:
                            tx_to_addrs[h].add(p)

    # Heuristik 2: gemeinsame Gegenparteien
    shared_cps: Dict[Tuple[str, str], int] = defaultdict(int)
    for chain_id, addr_map in per_chain_data.items():
        cps_by_addr: Dict[str, Set[str]] = {a: _counterparties_for(a, txs) for a, txs in addr_map.items()}
        for i in range(len(addrs)):
            for j in range(i+1, len(addrs)):
                a, b = addrs[i], addrs[j]
                inter = cps_by_addr.get(a, set()) & cps_by_addr.get(b, set())
                if inter:
                    shared_cps[(a, b)] += len(inter)

    # Clusterbildung: Union-Find über Kandidatenkanten
    parent = {a: a for a in addrs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    reasons_map: Dict[Tuple[str, str], List[str]] = defaultdict(list)

    # Kanten aus Co-occurrence: wenn beide Adressen im selben tx gesehen wurden
    for txh, parts in tx_to_addrs.items():
        overlap = [p for p in parts if p in addrs]
        for i in range(len(overlap)):
            for j in range(i+1, len(overlap)):
                a, b = overlap[i], overlap[j]
                union(a, b)
                reasons_map[tuple(sorted((a, b)))].append(f"co_occurrence_tx:{txh}")

    # Kanten aus gemeinsamen Gegenparteien
    for (a, b), cnt in shared_cps.items():
        if cnt >= min_shared_counterparties:
            union(a, b)
            reasons_map[tuple(sorted((a, b)))].append(f"shared_counterparties:{cnt}")

    # Cluster extrahieren
    groups: Dict[str, Set[str]] = defaultdict(set)
    for a in addrs:
        groups[find(a)].add(a)

    clusters: List[ClusterSuggestion] = []
    for root, members in groups.items():
        if len(members) <= 1:
            continue
        # Score: Kombination Co-occurrence-Edges und shared cps
        pair_reason_score = 0
        pairs = 0
        m = sorted(list(members))
        for i in range(len(m)):
            for j in range(i+1, len(m)):
                rs = reasons_map.get((m[i], m[j]), [])
                pair_reason_score += len(rs)
                pairs += 1
        score = pair_reason_score / max(pairs, 1)
        # Reasons: Top-K Gründe
        top_reasons = sorted({r for rs in reasons_map.values() for r in rs})[:10]
        clusters.append(ClusterSuggestion(members=m, score=round(score, 3), reasons=top_reasons))

    return {"clusters": [c.to_dict() for c in clusters], "analyzed": len(addrs)}
