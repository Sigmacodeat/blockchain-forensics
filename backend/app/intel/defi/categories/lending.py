from __future__ import annotations
from typing import List, Dict, Any


def list_protocols() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Aave",
            "slug": "aave",
            "category": "lending",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism", "avalanche"],
            "contracts": {},
            "tags": ["lending", "borrowing"],
        },
        {
            "name": "Compound",
            "slug": "compound",
            "category": "lending",
            "chains": ["ethereum"],
            "contracts": {},
            "tags": ["lending", "borrowing"],
        },
        {
            "name": "MakerDAO",
            "slug": "makerdao",
            "category": "lending",
            "chains": ["ethereum"],
            "contracts": {},
            "tags": ["cdp", "stablecoin", "dai"],
        },
    ]
