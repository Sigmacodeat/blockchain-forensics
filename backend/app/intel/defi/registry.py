from __future__ import annotations
import json
import os
from typing import Dict, List, Any, Iterable

from .categories import dex as cat_dex
from .categories import lending as cat_lending
from .categories import derivatives as cat_derivatives
from .categories import staking as cat_staking
from .categories import payments as cat_payments


Protocol = Dict[str, Any]


def _merge_protocols(*lists: Iterable[Protocol]) -> List[Protocol]:
    by_slug: Dict[str, Protocol] = {}
    for lst in lists:
        for p in lst:
            slug = p.get("slug") or p.get("name", "").lower().replace(" ", "-")
            if slug not in by_slug:
                by_slug[slug] = {**p, "slug": slug}
            else:
                # merge chains/tags/contracts
                base = by_slug[slug]
                base["chains"] = sorted(list(set(list(base.get("chains", [])) + list(p.get("chains", [])))))
                base["tags"] = sorted(list(set(list(base.get("tags", [])) + list(p.get("tags", [])))))
                # shallow contracts merge per chain
                contracts = base.get("contracts", {})
                for chain, arr in (p.get("contracts") or {}).items():
                    contracts.setdefault(chain, [])
                    # dedupe by address
                    seen = {c.get("address", "").lower() for c in contracts[chain]}
                    for c in arr:
                        addr = (c.get("address") or "").lower()
                        if addr and addr not in seen:
                            contracts[chain].append({**c, "address": addr})
                            seen.add(addr)
                base["contracts"] = contracts
    return list(by_slug.values())


def get_all_protocols() -> List[Protocol]:
    """Lädt die integrierten Protokoll-Definitionen (ohne externe Quellen)."""
    return _merge_protocols(
        cat_dex.list_protocols(),
        cat_lending.list_protocols(),
        cat_derivatives.list_protocols(),
        cat_staking.list_protocols(),
        cat_payments.list_protocols(),
    )


def _load_external_contracts() -> List[Dict[str, Any]]:
    """
    Optional: zusätzliche Contract-Listen laden.
    - ENV: DEFI_PROTOCOL_CONTRACT_SOURCES (JSON-Array von Dateipfaden oder URLs wird später ergänzt)
    - Hier zunächst nur lokale JSON-Dateipfade unterstützen.
    Format pro Datei: [{"slug": str, "chain": str, "address": str, "label": str, "type": str}]
    """
    items: List[Dict[str, Any]] = []
    val = os.getenv("DEFI_PROTOCOL_CONTRACT_SOURCES")
    if not val:
        return items
    try:
        sources = json.loads(val)
    except Exception:
        sources = []
    if not isinstance(sources, list):
        return items

    for src in sources:
        try:
            if isinstance(src, str) and os.path.isfile(src):
                with open(src, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for it in data:
                            if isinstance(it, dict):
                                items.append(it)
        except Exception:
            continue
    return items


def get_labels_seed() -> List[Dict[str, str]]:
    """
    Konvertiert Protokoll-Registry + externe Contracts in Label-Einträge für bulk_upsert.
    Gibt nur Einträge mit gültigen Addresses zurück.
    """
    protocols = get_all_protocols()
    extra_contracts = _load_external_contracts()

    # Index extra contracts by slug
    extras_by_slug: Dict[str, List[Dict[str, Any]]] = {}
    for it in extra_contracts:
        slug = str(it.get("slug") or "").strip().lower()
        if not slug:
            continue
        extras_by_slug.setdefault(slug, []).append(it)

    items: List[Dict[str, str]] = []

    for p in protocols:
        slug = p["slug"]
        name = p["name"]
        category = p["category"]

        # 1) Built-in contracts (often empty initially)
        contracts = p.get("contracts") or {}
        for chain, arr in contracts.items():
            for c in arr:
                addr = (c.get("address") or "").lower()
                if not addr:
                    continue
                label = c.get("label") or name
                items.append({
                    "chain": chain.lower(),
                    "address": addr,
                    "label": f"{name}",
                    "category": f"defi:{category}:{slug}",
                })

        # 2) External contracts merged by slug
        for c in extras_by_slug.get(slug, []):
            chain = str(c.get("chain") or "").lower()
            addr = str(c.get("address") or "").lower()
            if not chain or not addr:
                continue
            label = str(c.get("label") or name)
            items.append({
                "chain": chain,
                "address": addr,
                "label": label,
                "category": f"defi:{category}:{slug}",
            })

    # dedupe by (chain,address,label)
    seen = set()
    out: List[Dict[str, str]] = []
    for it in items:
        key = (it["chain"], it["address"], it["label"])
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out
