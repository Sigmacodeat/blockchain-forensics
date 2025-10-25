"""
Batch Bitcoin Script Analyzer
===============================

Erweitert den einzelnen TX-Analyzer um Batch-Verarbeitung mehrerer TXIDs.
Liefert aggregierte Statistiken und Flags.
"""

from __future__ import annotations
from typing import Any, Dict, List
from app.services.bitcoin_script_analyzer import bitcoin_script_analyzer
import logging

logger = logging.getLogger(__name__)


async def analyze_batch_scripts(txids: List[str]) -> Dict[str, Any]:
    """Analysiert mehrere Bitcoin-TXIDs in Batch und aggregiert Statistiken."""
    if not txids or len(txids) > 100:  # Limit für Performance
        return {"success": False, "message": "txids must be 1-100", "results": []}

    results = []
    aggregate = {
        "total_analyzed": 0,
        "success_count": 0,
        "error_count": 0,
        "script_types": {},
        "risk_flags": {},
        "high_risk_txs": [],
    }

    for txid in txids:
        try:
            res = await bitcoin_script_analyzer.analyze_tx(txid)
            results.append(res)

            if res.get("success"):
                aggregate["success_count"] += 1
                # Aggregiere Script-Typen
                for out in res.get("outputs", []):
                    st = out.get("type", "unknown")
                    aggregate["script_types"][st] = aggregate["script_types"].get(st, 0) + 1
                # Aggregiere Risk-Flags
                for out in res.get("outputs", []):
                    for flag in out.get("risk_hints", []):
                        aggregate["risk_flags"][flag] = aggregate["risk_flags"].get(flag, 0) + 1
                        if flag in ["nonstandard_script", "contains_op_return"]:
                            aggregate["high_risk_txs"].append(txid)
            else:
                aggregate["error_count"] += 1
        except Exception as e:
            logger.warning(f"Batch analysis failed for {txid}: {e}")
            results.append({"txid": txid, "success": False, "error": str(e)})
            aggregate["error_count"] += 1

    aggregate["total_analyzed"] = len(txids)
    aggregate["high_risk_count"] = len(set(aggregate["high_risk_txs"]))

    return {
        "success": True,
        "batch_size": len(txids),
        "results": results,
        "aggregate": aggregate,
    }
