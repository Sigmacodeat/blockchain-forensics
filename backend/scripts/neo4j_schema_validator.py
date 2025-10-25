#!/usr/bin/env python3
"""
Neo4j Schema Validator (Read-Only)
==================================

Prüft nicht-destruktiv, ob für die Heuristiken erwartete Labels/Properties vorhanden sind.

Nutzung:
  python backend/scripts/neo4j_schema_validator.py --chain ethereum

Hinweis:
- Es werden nur leichte COUNT/EXISTS-Queries ausgeführt.
- Keine Änderungen an Daten.
"""
import asyncio
import os
import sys
from typing import Dict, List, Tuple

# Allow running from repo root by adding backend/ to sys.path
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.neo4j_client import neo4j_client


CHECKS: List[Tuple[str, str]] = [
    ("bundles_present", "MATCH (t:Transaction) WHERE exists(t.in_private_bundle) RETURN count(t) as c"),
    ("sandwich_role_present", "MATCH (t:Transaction) WHERE exists(t.sandwich_role) RETURN count(t) as c"),
    ("function_calls_present", "MATCH (:Transaction)-[:CALLED_FUNCTION]->(f:Function) RETURN count(f) as c"),
    ("function_name_liquidation", "MATCH (:Transaction)-[:CALLED_FUNCTION]->(f:Function) WHERE toLower(f.name) CONTAINS 'liquidat' RETURN count(f) as c"),
    ("contract_protocols_set", "MATCH (c:Contract) WHERE exists(c.protocol) RETURN count(c) as c"),
    ("protocol_curve", "MATCH (c:Contract) WHERE toLower(c.protocol)='curve' RETURN count(c) as c"),
    ("protocol_yearn", "MATCH (c:Contract) WHERE toLower(c.protocol)='yearn' RETURN count(c) as c"),
    ("protocol_gmx", "MATCH (c:Contract) WHERE toLower(c.protocol)='gmx' RETURN count(c) as c"),
    ("gnosis_safe_type", "MATCH (c:Contract) WHERE toLower(c.type)='gnosis_safe' RETURN count(c) as c"),
    ("labels_tornado", "MATCH (:Address)-[:HAS_LABEL]->(l:Label) WHERE toLower(l.value) CONTAINS 'tornado' RETURN count(l) as c"),
    ("labels_aztec", "MATCH (:Address)-[:HAS_LABEL]->(l:Label) WHERE toLower(l.value) CONTAINS 'aztec' RETURN count(l) as c"),
    ("labels_railgun", "MATCH (:Address)-[:HAS_LABEL]->(l:Label) WHERE toLower(l.value) CONTAINS 'railgun' RETURN count(l) as c"),
]


async def run_checks() -> Dict[str, int]:
    results: Dict[str, int] = {}
    for name, query in CHECKS:
        try:
            rows = await neo4j_client.run_query(query, {})
            c = int(rows[0]["c"]) if rows else 0
            results[name] = c
        except Exception:
            results[name] = -1  # -1 = Query fehlgeschlagen
    return results


def classify(results: Dict[str, int]) -> List[str]:
    issues: List[str] = []
    # Minimalanforderungen für die aktivierten Heuristiken
    if results.get("function_calls_present", 0) == 0:
        issues.append("Keine Function-Call-Kanten gefunden (:Transaction)-[:CALLED_FUNCTION]->(Function)")
    if results.get("contract_protocols_set", 0) == 0:
        issues.append("Keine Contract.protocol Felder gefunden – Protokoll-basierte Heuristiken werden nichts finden")
    if results.get("bundles_present", 0) == 0:
        issues.append("Transaction.in_private_bundle fehlt – Flashbots/Private Bundle Heuristik eingeschränkt")
    if results.get("sandwich_role_present", 0) == 0:
        issues.append("Transaction.sandwich_role fehlt – Sandwich-Attack Heuristik eingeschränkt")
    if results.get("labels_tornado", 0) == 0:
        issues.append("Keine 'tornado' Labels – Mixer-Timing-Heuristik eingeschränkt")
    # Hinweise (nicht kritisch)
    for proto in ["protocol_curve", "protocol_yearn", "protocol_gmx"]:
        if results.get(proto, 0) == 0:
            issues.append(f"Hinweis: {proto} = 0 – prüfe Contract.protocol Normalisierung")
    if results.get("gnosis_safe_type", 0) == 0:
        issues.append("Hinweis: Contract.type='gnosis_safe' nicht gefunden – Gnosis Safe Heuristik eingeschränkt")
    return issues


async def main():
    results = await run_checks()
    print("\nNeo4j Schema Validator Report")
    print("============================")
    for k in sorted(results.keys()):
        v = results[k]
        print(f"- {k}: {v if v >= 0 else 'QUERY_FAILED'}")
    issues = classify(results)
    print("\nAssessment")
    print("----------")
    if issues:
        for m in issues:
            print(f"- {m}")
    else:
        print("- OK: Alle Kern-Properties/Labels wurden gefunden.")


if __name__ == "__main__":
    # Keine CLI-Parameter nötig – globaler Überblick
    asyncio.run(main())
