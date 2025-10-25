"""
DeFi Labels Ingestion
- Nutzt die modulare Registry (backend/app/intel/defi/registry.py)
- Optional: Zusätzliche Contracts via ENV DEFI_PROTOCOL_CONTRACT_SOURCES (Liste lokaler JSON-Dateien)
- Schreibt Labels via labels_repo.bulk_upsert
"""
from __future__ import annotations
import asyncio
import os
from typing import Dict

from app.intel.defi.registry import get_labels_seed
from app.repos.labels_repo import bulk_upsert


async def run_once(dry_run: bool = False) -> Dict[str, int]:
    """Führt die DeFi-Labels-Ingestion aus.

    - dry_run=True: keine DB-Schreibvorgänge, nur Zählwerte zurückgeben
    - dry_run kann auch via ENV DRY_RUN=1 aktiviert werden
    """
    items = get_labels_seed()
    if not items:
        return {"inserted": 0, "existing": 0, "total": 0, "dry_run": int(bool(dry_run or os.getenv("DRY_RUN") == "1"))}

    effective_dry_run = dry_run or os.getenv("DRY_RUN") == "1"
    if effective_dry_run:
        # Keine DB-Schreibvorgänge durchführen
        return {"inserted": 0, "existing": 0, "total": len(items), "dry_run": 1}

    inserted, existing = await bulk_upsert(items)
    return {"inserted": inserted, "existing": existing, "total": len(items), "dry_run": 0}


if __name__ == "__main__":
    print(asyncio.run(run_once()))
