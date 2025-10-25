from __future__ import annotations
from typing import List, Dict, Any


def list_protocols() -> List[Dict[str, Any]]:
    return [
        {
            "name": "GMX",
            "slug": "gmx",
            "category": "derivatives",
            "chains": ["arbitrum", "avalanche"],
            "contracts": {},
            "tags": ["perps", "derivatives"],
        },
        {
            "name": "dYdX",
            "slug": "dydx",
            "category": "derivatives",
            "chains": ["dydx"],
            "contracts": {},
            "tags": ["perps", "orderbook"],
        },
    ]
