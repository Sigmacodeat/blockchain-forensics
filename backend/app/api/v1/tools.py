from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user_strict

router = APIRouter(prefix="/tools", tags=["Tools Registry"]) 


@router.get("/registry")
async def list_tools_registry(_user: Dict[str, Any] = Depends(get_current_user_strict)) -> Dict[str, Any]:
    """Liefert eine kuratierte Liste externer Open-Source/Explorer-Tools (Meta-Registry)."""
    registry: Dict[str, List[Dict[str, str]]] = {
        "explorers": [
            {"name": "Etherscan", "url": "https://etherscan.io"},
            {"name": "Blockchair", "url": "https://blockchair.com"},
            {"name": "Mempool.space (BTC)", "url": "https://mempool.space"},
            {"name": "Solscan", "url": "https://solscan.io"},
        ],
        "data": [
            {"name": "Dune", "url": "https://dune.com"},
            {"name": "Google BigQuery public crypto datasets", "url": "https://console.cloud.google.com/marketplace/browse?filter=solution-type:dataset&q=crypto"},
        ],
        "forensics": [
            {"name": "BlockSci", "url": "https://github.com/citp/BlockSci"},
            {"name": "GraphSense", "url": "https://github.com/graphsense/graphsense"},
            {"name": "bitcoin script debugger (btcdeb)", "url": "https://github.com/kallewoof/btcdeb"},
        ],
    }
    return {"registry": registry, "total_categories": len(registry)}
