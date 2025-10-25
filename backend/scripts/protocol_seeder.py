#!/usr/bin/env python3
"""
Contract Protocol Seeder (Neo4j)
================================

- Liest eine CSV (address,protocol) und setzt `Contract.protocol` für bekannte DeFi‑Contracts.
- Default: DRY‑RUN (zeigt geplante Änderungen). Mit `--apply` werden Properties gesetzt.

Usage:
  python backend/scripts/protocol_seeder.py --csv backend/scripts/protocol_seed.csv [--apply]

CSV Format (header required):
  address,protocol
  0x1111111254eeb25477B68fb85Ed929f73A960582,uniswap
  0xb9446c4Ef5EBE66268dA6700D26f96273DE3d571,curve
"""
import csv
import os
import sys
import argparse
import asyncio
from typing import List, Tuple

# sys.path for repo-root execution
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.neo4j_client import neo4j_client  # type: ignore


async def load_csv(path: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for rec in r:
            addr = (rec.get("address") or "").strip().lower()
            proto = (rec.get("protocol") or "").strip().lower()
            if addr and proto:
                rows.append((addr, proto))
    return rows


async def apply_protocol(address: str, protocol: str, dry_run: bool) -> bool:
    query = (
        "MATCH (c:Contract {address: $address}) "
        "SET c.protocol = $protocol "
        "RETURN c.address as address"
    )
    if dry_run:
        # Existence check only
        check = "MATCH (c:Contract {address: $address}) RETURN count(c) as cnt"
        res = await neo4j_client.run_query(check, {"address": address})
        cnt = int(res[0]["cnt"]) if res else 0
        print(f"DRY-RUN: address={address} exists={cnt>0}, protocol={protocol}")
        return cnt > 0
    else:
        res = await neo4j_client.run_query(query, {"address": address, "protocol": protocol})
        ok = bool(res)
        print(f"APPLIED: address={address}, protocol={protocol}, ok={ok}")
        return ok


async def main(csv_path: str, apply_flag: bool):
    pairs = await load_csv(csv_path)
    if not pairs:
        print("No rows found in CSV.")
        return
    print(f"Loaded {len(pairs)} mappings from {csv_path}. apply={apply_flag}")
    ok_count = 0
    for addr, proto in pairs:
        ok = await apply_protocol(addr, proto, dry_run=not apply_flag)
        if ok:
            ok_count += 1
    print(f"Done. Success/checked: {ok_count}/{len(pairs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to protocol mapping CSV")
    parser.add_argument("--apply", action="store_true", help="Apply changes (otherwise dry-run)")
    args = parser.parse_args()
    asyncio.run(main(args.csv, args.apply))
