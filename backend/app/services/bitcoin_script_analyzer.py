"""
Bitcoin Script Analyzer (lightweight)
=====================================

Analysiert Bitcoin-Transaktionen auf Script-Ebene basierend auf JSON-RPC (getrawtransaction verbose).
Keine externen Abhängigkeiten außer unserem BitcoinAdapter.

Features:
- Klassifikation von scriptPubKey-Typen (p2pkh, p2sh, v0_p2wpkh, v0_p2wsh, nulldata, multisig, nonstandard)
- Extrahiert ASM und schätzt Risiken (OP_RETURN, nonstandard)
- Liefert strukturierte Analyse pro Input/Output
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def _classify_script_type(spk: Dict[str, Any]) -> str:
    t = (spk or {}).get("type") or ""
    t = str(t).lower()
    if t in {"pubkeyhash", "p2pkh"}:
        return "p2pkh"
    if t in {"scripthash", "p2sh"}:
        return "p2sh"
    if t in {"witness_v0_keyhash", "v0_p2wpkh"}:
        return "v0_p2wpkh"
    if t in {"witness_v0_scripthash", "v0_p2wsh"}:
        return "v0_p2wsh"
    if t in {"nulldata", "op_return"}:
        return "op_return"
    if t in {"multisig"}:
        return "multisig"
    if t:
        return t
    return "unknown"


def _risk_hints_for_output(spk: Dict[str, Any]) -> List[str]:
    hints: List[str] = []
    t = _classify_script_type(spk)
    if t == "op_return":
        hints.append("contains_op_return")
    if t in {"nonstandard", "unknown"}:
        hints.append("nonstandard_script")
    return hints


def _risk_hints_for_input(ss: Dict[str, Any]) -> List[str]:
    hints: List[str] = []
    asm = (ss or {}).get("asm") or ""
    if "OP_RETURN" in asm:
        hints.append("asm_contains_op_return")
    # Add-on: anyonecanpay flag is in witness flags, not here. Skipped.
    return hints


class BitcoinScriptAnalyzer:
    def __init__(self) -> None:
        try:
            from app.adapters.bitcoin_adapter import BitcoinAdapter  # lazy import
            self._adapter = BitcoinAdapter()
        except Exception as e:
            logger.warning(f"BitcoinAdapter unavailable: {e}")
            self._adapter = None

    async def analyze_tx(self, txid: str) -> Dict[str, Any]:
        if not self._adapter:
            return {"success": False, "message": "Bitcoin RPC not configured", "txid": txid}

        raw = await self._adapter.fetch_tx(txid)
        if not raw or raw.get("txid") != txid:
            return {"success": False, "message": "Transaction not found", "txid": txid}

        vins = raw.get("vin", []) or []
        vouts = raw.get("vout", []) or []

        inputs: List[Dict[str, Any]] = []
        for vin in vins:
            ss = vin.get("scriptSig") or {}
            inputs.append({
                "txid": vin.get("txid"),
                "vout": vin.get("vout"),
                "coinbase": bool(vin.get("coinbase")),
                "script_asm": ss.get("asm"),
                "script_hex": ss.get("hex"),
                "risk_hints": _risk_hints_for_input(ss),
            })

        outputs: List[Dict[str, Any]] = []
        for vout in vouts:
            spk = (vout or {}).get("scriptPubKey") or {}
            outputs.append({
                "n": vout.get("n"),
                "value": vout.get("value"),
                "addresses": spk.get("addresses") or ([spk.get("address")] if spk.get("address") else []),
                "type": _classify_script_type(spk),
                "asm": spk.get("asm"),
                "risk_hints": _risk_hints_for_output(spk),
            })

        return {
            "success": True,
            "txid": txid,
            "input_count": len(inputs),
            "output_count": len(outputs),
            "inputs": inputs,
            "outputs": outputs,
        }


bitcoin_script_analyzer = BitcoinScriptAnalyzer()
