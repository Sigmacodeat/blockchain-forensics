"""
Labels Ingestion Pipeline
- Multi-Sanctions (OFAC/UN/EU/UK)
- Public Exchange/Service labels (seed)
- Bulk Upsert via labels_repo.bulk_upsert
"""
from __future__ import annotations
import asyncio
from typing import List, Dict
import os
import json
import csv
from io import StringIO
import httpx

from app.repos.labels_repo import bulk_upsert
from app.compliance.sources.sanctions_indexer import sanctions_indexer


async def fetch_ofac_addresses() -> List[Dict[str, str]]:
    # Use the new sanctions indexer
    all_sanctions = await sanctions_indexer.get_normalized_data()
    return [
        {
            'chain': item['chain'],
            'address': item['address'],
            'label': item['label'],
            'category': item['category']
        }
        for item in all_sanctions
        if item['source'] == 'OFAC'
    ]


async def fetch_un_addresses() -> List[Dict[str, str]]:
    all_sanctions = await sanctions_indexer.get_normalized_data()
    return [
        {
            'chain': item['chain'],
            'address': item['address'],
            'label': item['label'],
            'category': item['category']
        }
        for item in all_sanctions
        if item['source'] == 'UN'
    ]


async def fetch_eu_addresses() -> List[Dict[str, str]]:
    all_sanctions = await sanctions_indexer.get_normalized_data()
    return [
        {
            'chain': item['chain'],
            'address': item['address'],
            'label': item['label'],
            'category': item['category']
        }
        for item in all_sanctions
        if item['source'] == 'EU'
    ]


async def fetch_uk_addresses() -> List[Dict[str, str]]:
    all_sanctions = await sanctions_indexer.get_normalized_data()
    return [
        {
            'chain': item['chain'],
            'address': item['address'],
            'label': item['label'],
            'category': item['category']
        }
        for item in all_sanctions
        if item['source'] == 'UK'
    ]


async def fetch_exchange_seeds() -> List[Dict[str, str]]:
    """Fetch public exchange/service label seeds from configured sources.

    Sources can be provided via:
    - Env EXCHANGE_LABEL_SOURCES: JSON array of URLs
    - Default: empty list; in TEST_MODE returns a small canned sample

    Supported formats per URL:
    - JSON array of {chain,address,label,category}
    - CSV with headers: chain,address,label,category
    """
    # Configuration
    urls: List[str] = []
    env_val = os.getenv("EXCHANGE_LABEL_SOURCES")
    if env_val:
        try:
            parsed = json.loads(env_val)
            if isinstance(parsed, list):
                urls = [str(u) for u in parsed]
        except Exception:
            urls = []

    # TEST_MODE fallback: return small static set when no sources configured
    if not urls and (os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")):
        return [
            {"chain": "ethereum", "address": "0x0000000000000000000000000000000000000000", "label": "Null", "category": "system"},
            {"chain": "ethereum", "address": "0x5a52e96bacdabb82fd05763e25335261b270efcb", "label": "OKX", "category": "exchange"},
        ]

    if not urls:
        return []

    items: List[Dict[str, str]] = []
    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    continue
                ctype = resp.headers.get("content-type", "").lower()
                text = resp.text
                # JSON
                if "application/json" in ctype or text.strip().startswith("["):
                    try:
                        data = resp.json()
                        if isinstance(data, list):
                            for it in data:
                                if not isinstance(it, dict):
                                    continue
                                items.append({
                                    "chain": str(it.get("chain") or "").lower(),
                                    "address": str(it.get("address") or "").lower(),
                                    "label": str(it.get("label") or "").strip(),
                                    "category": str(it.get("category") or "generic").strip(),
                                })
                        continue
                    except Exception:
                        pass
                # CSV
                if "text/csv" in ctype or "," in text[:100]:
                    try:
                        sio = StringIO(text)
                        reader = csv.DictReader(sio)
                        for row in reader:
                            items.append({
                                "chain": str((row.get("chain") or "")).lower(),
                                "address": str((row.get("address") or "")).lower(),
                                "label": str((row.get("label") or "")).strip(),
                                "category": str((row.get("category") or "generic")).strip(),
                            })
                        continue
                    except Exception:
                        pass
            except Exception:
                continue
    # Normalize and filter invalid
    return _normalize(items)


def _normalize(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for it in items:
        chain = (it.get("chain") or "").lower()
        addr = (it.get("address") or "").lower()
        label = (it.get("label") or "").strip()
        category = (it.get("category") or "generic").strip()
        if not chain or not addr or not label:
            continue
        out.append({
            "chain": chain,
            "address": addr,
            "label": label,
            "category": category,
        })
    return out


async def run_once() -> Dict[str, int]:
    tasks = await asyncio.gather(
        fetch_ofac_addresses(),
        fetch_un_addresses(),
        fetch_eu_addresses(),
        fetch_uk_addresses(),
        fetch_exchange_seeds(),
        return_exceptions=False,
    )

    merged: List[Dict[str, str]] = []
    for lst in tasks:
        merged.extend(lst)

    normalized = _normalize(merged)
    inserted, existing = await bulk_upsert(normalized)
    return {"inserted": inserted, "existing": existing, "total": len(normalized)}


if __name__ == "__main__":
    # Simple local runner
    print(asyncio.run(run_once()))
