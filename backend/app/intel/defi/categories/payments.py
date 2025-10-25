from __future__ import annotations
from typing import List, Dict, Any


def list_protocols() -> List[Dict[str, Any]]:
    return [
        {
            "name": "0x",
            "slug": "0x",
            "category": "payments",
            "chains": ["ethereum", "polygon", "bsc", "avalanche"],
            "contracts": {},
            "tags": ["aggregator", "dex-aggregator"],
        },
        {
            "name": "1inch",
            "slug": "1inch",
            "category": "payments",
            "chains": ["ethereum", "polygon", "bsc", "avalanche", "arbitrum", "optimism"],
            "contracts": {},
            "tags": ["aggregator", "dex-aggregator"],
        },
    ]
