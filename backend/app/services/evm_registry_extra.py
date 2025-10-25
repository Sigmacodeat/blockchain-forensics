"""
EVM Registry Extra Loader
- Lädt zusätzliche EVM-Chains dynamisch von chainid.network
- Liefert ein Dict[str, ChainInfo]-kompatibles Mapping (chain_key -> ChainInfo-ähnliche Felder)
"""
from __future__ import annotations
from typing import Dict, Any, List
import httpx


async def fetch_chainid_chains(limit: int = 50) -> List[dict]:
    url = "https://chainid.network/chains.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data[:limit]


def _is_testnet(name: str) -> bool:
    n = (name or "").lower()
    return any(k in n for k in ["testnet", "goerli", "sepolia", "holesky", "chiado", "mumbai", "rinkeby", "kovan"]) 


async def load_extra_evm_chains() -> Dict[str, Dict[str, Any]]:
    """
    Liefert ein Mapping im Format:
    {
      chain_key: {
        "chain_id": str,
        "name": str,
        "symbol": str,
        "rpc_urls": List[str],
        "explorer": str,
        "native_currency": {"name": str, "symbol": str, "decimals": int},
        "features": List[str]
      }
    }
    """
    out: Dict[str, Dict[str, Any]] = {}
    try:
        chains = await fetch_chainid_chains(50)
    except Exception:
        return out

    for ch in chains:
        name = ch.get("title") or ch.get("name") or str(ch.get("chainId"))
        if _is_testnet(name):
            continue
        chain_key = (ch.get("name") or str(ch.get("chainId"))).strip()
        native = ch.get("nativeCurrency", {})
        symbol = native.get("symbol", "ETH")
        decimals = int(native.get("decimals", 18))
        rpcs = [r for r in ch.get("rpc", []) if isinstance(r, str)]
        explorers = ch.get("explorers", [])
        explorer_url = explorers[0].get("url", "") if explorers else ""

        out[chain_key] = {
            "chain_id": chain_key,
            "name": name,
            "symbol": symbol,
            "rpc_urls": rpcs,
            "explorer": explorer_url,
            "native_currency": {"name": name, "symbol": symbol, "decimals": decimals},
            "features": ["evm"],
        }
    return out
