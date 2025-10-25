from __future__ import annotations
from typing import List, Dict, Any


def list_protocols() -> List[Dict[str, Any]]:
    """
    DEX-Protokolle (Startset, erweiterbar):
    - Nur Metadaten, keine Hardcoded-Contract-Adressen.
    - Adressen können via externe Quellen/JSON ergänzt werden.
    """
    return [
        {
            "name": "Uniswap V3",
            "slug": "uniswap-v3",
            "category": "dex",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism", "base"],
            "contracts": {},
            "tags": ["amm", "v3", "concentrated-liquidity"],
        },
        {
            "name": "Curve",
            "slug": "curve",
            "category": "dex",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism", "fantom"],
            "contracts": {},
            "tags": ["stablecoin", "amm", "metapools"],
        },
        {
            "name": "SushiSwap",
            "slug": "sushiswap",
            "category": "dex",
            "chains": ["ethereum", "polygon", "arbitrum", "bsc", "fantom"],
            "contracts": {},
            "tags": ["amm"],
        },
        {
            "name": "Balancer",
            "slug": "balancer",
            "category": "dex",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism"],
            "contracts": {},
            "tags": ["amm", "weighted-pools"],
        },
        {
            "name": "PancakeSwap",
            "slug": "pancakeswap",
            "category": "dex",
            "chains": ["bsc", "ethereum", "aptos"],
            "contracts": {},
            "tags": ["amm"],
        },
    ]
