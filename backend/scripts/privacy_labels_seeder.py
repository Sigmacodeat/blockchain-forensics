#!/usr/bin/env python3
"""
Privacy Labels Seeder (Neo4j)
=============================

- Liest eine CSV (address,label) und setzt Privacy-/Mixer-Labels wie 'tornado', 'aztec', 'railgun'.
- Default: DRY-RUN (zeigt geplante Änderungen). Mit `--apply` werden Knoten/Relationen gemerged.

Usage:
  python backend/scripts/privacy_labels_seeder.py --csv backend/scripts/privacy_labels_seed.csv [--apply]

CSV Format (header required):
  address,label
  0x1111111111111111111111111111111111111111,tornado
  0x2222222222222222222222222222222222222222,aztec
  0x3333333333333333333333333333333333333333,railgun
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


ALLOWED_LABELS = {"tornado", "aztec", "railgun", "mixer", "privacy"}


async def load_csv(path: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for rec in r:
            addr = (rec.get("address") or "").strip().lower()
            label = (rec.get("label") or "").strip().lower()
            if addr and label:
                rows.append((addr, label))
    return rows


async def dry_check(address: str, label: str) -> str:
    # Check address exists, and if label relation already present
    q = (
        "MATCH (a:Address {address: $address}) "
        "OPTIONAL MATCH (a)-[:HAS_LABEL]->(l:Label) "
        "RETURN a IS NOT NULL AS addr_exists, any(x IN collect(l.value) WHERE toLower(x)=$label) AS has_label"
    )
    res = await neo4j_client.run_query(q, {"address": address, "label": label})
    if not res:
        return "addr_exists=False, has_label=False"
    r = res[0]
    return f"addr_exists={bool(r.get('addr_exists'))}, has_label={bool(r.get('has_label'))}"


async def apply_label(address: str, label: str, dry_run: bool) -> bool:
    if dry_run:
        info = await dry_check(address, label)
        print(f"DRY-RUN: address={address}, label={label} | {info}")
        return True
    else:
        q = (
            "MATCH (a:Address {address: $address}) "
            "MERGE (l:Label {value: $label}) "
            "MERGE (a)-[:HAS_LABEL]->(l) "
            "RETURN a.address as address"
        )
        res = await neo4j_client.run_query(q, {"address": address, "label": label})
        ok = bool(res)
        print(f"APPLIED: address={address}, label={label}, ok={ok}")
        return ok


async def main(csv_path: str, apply_flag: bool):
    pairs = await load_csv(csv_path)
    if not pairs:
        print("No rows found in CSV.")
        return
    # Warn about unknown labels
    unknown = sorted({label for _, label in pairs if label not in ALLOWED_LABELS})
    if unknown:
        print(f"WARNING: Unknown labels in CSV (will still apply): {', '.join(unknown)}")
    print(f"Loaded {len(pairs)} label mappings from {csv_path}. apply={apply_flag}")
    ok_count = 0
    for addr, label in pairs:
        ok = await apply_label(addr, label, dry_run=not apply_flag)
        if ok:
            ok_count += 1
    print(f"Done. Success/checked: {ok_count}/{len(pairs)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to labels CSV")
    parser.add_argument("--apply", action="store_true", help="Apply changes (otherwise dry-run)")
    args = parser.parse_args()
    asyncio.run(main(args.csv, args.apply))
