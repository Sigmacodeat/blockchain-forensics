#!/usr/bin/env python3
"""
Heuristics Smoke Test
=====================

Usage:
  python backend/scripts/heuristics_smoketest.py --chain ethereum 0xaddr1 0xaddr2 ...

Description:
- Läuft die Heuristiken über gegebene Adressen und druckt eine kompakte Zusammenfassung.
- Nicht-destruktiv. Erwartet, dass Neo4j/Postgres Verbindungen konfiguriert sind.
"""
import asyncio
import argparse
from typing import List

from app.ml.heuristics_library import heuristics_lib
from app.db.neo4j_client import neo4j_client
from app.db.postgres_client import postgres_client


async def run_for_address(address: str, chain: str):
    results = await heuristics_lib.run_all_heuristics(
        address=address,
        chain=chain,
        neo4j_client=neo4j_client,
        postgres_client=postgres_client,
    )
    # Aggregate
    total_related = set()
    summary = []
    for name, res in results.items():
        if not res:
            continue
        if res.related_addresses:
            total_related.update(res.related_addresses)
            evidence_sample = ", ".join(res.evidence[:2]) if res.evidence else ""
            summary.append((name, res.confidence, len(res.related_addresses), evidence_sample))
    # Sort by confidence then count
    summary.sort(key=lambda x: (-x[1], -x[2]))

    print(f"\n=== Address: {address} | Chain: {chain} ===")
    print(f"Heuristics fired: {len(summary)} | Unique related addresses: {len(total_related)}")
    for name, conf, cnt, ev in summary[:10]:
        print(f" - {name}: conf={conf:.2f}, related={cnt}{' | ' + ev if ev else ''}")


async def main(addresses: List[str], chain: str):
    for addr in addresses:
        await run_for_address(addr, chain)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("addresses", nargs="+", help="Blockchain addresses")
    parser.add_argument("--chain", default="ethereum", help="Chain (ethereum, bitcoin, polygon, ...)")
    args = parser.parse_args()
    asyncio.run(main(args.addresses, args.chain))
