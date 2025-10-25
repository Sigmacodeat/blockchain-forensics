from __future__ import annotations
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import logging

logger = logging.getLogger(__name__)

# Simple static source weights; can be moved to config or DB later
SOURCE_WEIGHTS: Dict[str, float] = {
    "rekt": 0.9,
    "slowmist": 0.85,
    "chainabuse": 0.75,
    "etherscan": 0.6,
    "defillama": 0.65,
}

# Expected unified item format from connectors
# { chain: str, address: str, label: str, category: str, source: str }


def _pick(d: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _unify_item_fields(source: str, r: Dict[str, Any]) -> Dict[str, Any]:
    """Versucht generisch Felder zu vereinheitlichen aus heterogenen Quellen.
    Erkennt alternative Feldnamen und setzt Defaults.
    """
    ch = _pick(r, ["chain", "network", "blockchain"]) or ""
    addr = _pick(r, ["address", "addr", "wallet", "account", "to", "from"]) or ""
    lbl = _pick(r, ["label", "tag", "name", "note", "category"]) or ""
    cat = _pick(r, ["category", "type", "class"]) or "generic"
    item = {
        "chain": str(ch).lower(),
        "address": str(addr).lower(),
        "label": str(lbl),
        "category": str(cat) if cat else "generic",
        "source": source,
    }
    return item


def _read_local_feed(name: str) -> List[Dict[str, Any]]:
    base = Path(os.getcwd()) / "data" / "label_feeds"
    p = base / f"{name}.json"
    if not p.exists():
        logger.info(f"Label feed not found (skip): {p}")
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and data.get("items"):
            return list(data.get("items") or [])
    except Exception as e:
        logger.warning(f"Failed to read feed {name}: {e}")
    return []


def _fetch_remote_feed_sync(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> List[Dict[str, Any]]:
    """Synchroner HTTP-JSON-Fetch (stdlib), wird asynchron via to_thread aufgerufen.
    Erwartet eine Liste oder ein Dict mit Schlüssel 'items'.
    """
    try:
        import urllib.request
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 (trusted URLs via env)
            data = resp.read()
            text = data.decode("utf-8", errors="ignore")
            obj = json.loads(text)
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict) and obj.get("items"):
                return list(obj.get("items") or [])
    except Exception as e:
        logger.warning(f"Failed to fetch remote feed {url}: {e}")
    return []


async def _read_remote_feeds(name: str, urls: Union[str, List[str]], headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    if isinstance(urls, str):
        urls = [urls]
    results: List[Dict[str, Any]] = []
    for u in urls:
        try:
            items = await asyncio.to_thread(_fetch_remote_feed_sync, u, headers)
            for r in items:
                rr = _unify_item_fields(name, dict(r))
                results.append(rr)
        except Exception as e:
            logger.warning(f"Remote read failed for {name} {u}: {e}")
    return results


async def fetch_sources(sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    wanted = sources or list(SOURCE_WEIGHTS.keys())
    items: List[Dict[str, Any]] = []

    # Remote config via ENV (JSON): { "rekt": "https://...", "slowmist": ["https://...", "https://..."] }
    remote_cfg_raw = os.getenv("LABEL_FEEDS_URLS_JSON", "{}")
    try:
        remote_cfg: Dict[str, Union[str, List[str]]] = json.loads(remote_cfg_raw)
    except Exception:
        remote_cfg = {}

    # Optional headers via ENV (JSON): { "Authorization": "Bearer ..." }
    remote_headers_raw = os.getenv("LABEL_FEEDS_HEADERS_JSON", "{}")
    try:
        remote_headers: Dict[str, str] = json.loads(remote_headers_raw)
    except Exception:
        remote_headers = {}

    # Fetch remote if configured
    for src in wanted:
        if src in remote_cfg:
            remote = await _read_remote_feeds(src, remote_cfg[src], headers=remote_headers)
            for r in remote:
                items.append(_unify_item_fields(src, r))

    # Local/offline fallback
    for src in wanted:
        rows = _read_local_feed(src)
        for r in rows:
            items.append(_unify_item_fields(src, dict(r)))
    return items


def normalize_and_dedupe(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Normalize and dedupe by (chain,address,label). Compute simple trust score per key.
    Returns (items, stats)
    """
    key_seen: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    sources_per_key: Dict[Tuple[str, str, str], Set[str]] = {}

    for r in rows:
        ch = (r.get("chain") or "").lower()
        addr = (r.get("address") or "").lower()
        lbl = r.get("label") or ""
        cat = r.get("category") or "generic"
        src = r.get("source") or "unknown"
        key = (ch, addr, lbl)
        if key not in key_seen:
            key_seen[key] = {"chain": ch, "address": addr, "label": lbl, "category": cat}
            sources_per_key[key] = set()
        sources_per_key[key].add(src)

    # compute trust scores (not persisted yet; reserved for future repo support)
    trust: Dict[Tuple[str, str, str], float] = {}
    for k, srcs in sources_per_key.items():
        score = 0.0
        if srcs:
            score = sum(SOURCE_WEIGHTS.get(s, 0.5) for s in srcs) / float(len(srcs))
        trust[k] = score

    items = list(key_seen.values())
    stats = {
        "input": len(rows),
        "unique": len(items),
        "sources": {k: len(v) for k, v in sources_per_key.items()},
        "avg_trust": (sum(trust.values())/len(trust) if trust else 0.0),
    }
    return items, stats


async def aggregate_label_feeds(sources: Optional[List[str]] = None) -> Dict[str, Any]:
    rows = await fetch_sources(sources)
    items, stats = normalize_and_dedupe(rows)
    # Persist via repo (best-effort)
    try:
        from app.repos.labels_repo import bulk_upsert
        inserted, _ = await bulk_upsert(items)
    except Exception as e:
        logger.warning(f"bulk_upsert failed (continue): {e}")
        inserted = 0
    return {"inserted": inserted, **stats}
