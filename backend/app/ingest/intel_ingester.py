"""
Intel Ingestion Pipeline
- Persistiert recente Inbound-Intel-Events als Labels via labels_repo.bulk_upsert
- Aktualisiert Risk-Scores für betroffene Adressen (best-effort)
"""
from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from app.integrations.feeds import threat_intel_service
from app.repos.labels_repo import bulk_upsert
from app.services.risk_service import service as risk_service


def _extract_labels_from_event(ev: Dict[str, Any]) -> List[Dict[str, str]]:
    """Versucht, aus einem generischen Intel-Event label-ähnliche Einträge zu extrahieren.
    Erwartete Strukturen (analog zu Sanctions-Ingest):
    - {"addresses": ["0x..."], "chain": "ethereum", "label": "...", "category": "..."}
    - {"items": [{"address": "0x...", "chain": "...", "label": "...", "category": "..."}]}
    - {"entries": [...]}
    Falls keine Struktur passt, wird eine leere Liste zurückgegeben.
    """
    payload = ev.get("event") or ev.get("event_data") or ev.get("event_payload") or {}
    if not isinstance(payload, dict):
        payload = {}
    source = (ev.get("source") or ev.get("event") or {}).get("source") if isinstance(ev.get("event"), dict) else ev.get("source")
    src = str(source or "INTEL").upper()

    labels: List[Dict[str, str]] = []
    try:
        # Variante 1: flache Liste
        if isinstance(payload.get("addresses"), list):
            chain = str(payload.get("chain") or "ethereum").lower()
            label = str(payload.get("label") or "intel_flag").strip() or "intel_flag"
            category = str(payload.get("category") or src).strip() or src
            for addr in payload["addresses"]:
                a = str(addr or "").lower()
                if a:
                    labels.append({"chain": chain, "address": a, "label": label, "category": category})
        # Variante 2/3: items/entries
        for key in ("items", "entries"):
            if isinstance(payload.get(key), list):
                for it in payload[key]:
                    chain = str((it or {}).get("chain") or payload.get("chain") or "ethereum").lower()
                    addr = str((it or {}).get("address") or "").lower()
                    label = str((it or {}).get("label") or payload.get("label") or "intel_flag").strip() or "intel_flag"
                    category = str((it or {}).get("category") or payload.get("category") or src).strip() or src
                    if addr:
                        labels.append({"chain": chain, "address": addr, "label": label, "category": category})
    except Exception:
        return []

    return labels


async def persist_recent(limit: int = 1000) -> Dict[str, int]:
    """Persistiert die letzten Inbound-Events in Labels und refresht Risk-Scores.
    Returns: {inserted, existing, total, scored}
    """
    events = threat_intel_service.recent_inbound_events(limit=limit)
    to_upsert: List[Dict[str, str]] = []
    addrs: List[str] = []
    for ev in events:
        labels = _extract_labels_from_event(ev)
        to_upsert.extend(labels)
        for l in labels:
            a = l.get("address")
            if a:
                addrs.append(a)
    if not to_upsert:
        return {"inserted": 0, "existing": 0, "total": 0, "scored": 0}

    inserted, existing = await bulk_upsert(to_upsert)

    # Risk-Scores aktualisieren (best-effort, entkoppelt)
    uniq_addrs = sorted(list({a for a in addrs if a}))
    async def _score(a: str):
        try:
            # Kette hier unbekannt -> gängigste Default-Kette verwenden (ethereum). In echten Setups anhand labels ableiten.
            await risk_service.score_address("ethereum", a)
        except Exception:
            return
    await asyncio.gather(*[_score(a) for a in uniq_addrs])

    return {"inserted": int(inserted), "existing": int(existing), "total": len(to_upsert), "scored": len(uniq_addrs)}
