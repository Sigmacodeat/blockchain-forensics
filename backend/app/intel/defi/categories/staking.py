from __future__ import annotations
from typing import List, Dict, Any


def list_protocols() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Lido",
            "slug": "lido",
            "category": "staking",
            "chains": ["ethereum", "polygon", "solana"],
            "contracts": {},
            "tags": ["liquid-staking", "steth"],
        },
        {
            "name": "Rocket Pool",
            "slug": "rocket-pool",
            "category": "staking",
            "chains": ["ethereum"],
            "contracts": {},
            "tags": ["liquid-staking", "reth"],
        },
    ]
