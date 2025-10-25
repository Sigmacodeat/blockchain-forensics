"""Scroll Adapter - EVM-kompatibel (ZK Rollup)"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any

from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class ScrollAdapter(EthereumAdapter):
    """Scroll blockchain adapter – EVM-kompatibel"""

    def __init__(self, rpc_url: Optional[str] = None):
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, "SCROLL_RPC_URL", None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://scroll")
        self._chain_name = "scroll"
        logger.info(f"Initialized Scroll adapter with RPC: {self.rpc_url}")

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """Scroll-spezifische Bridge-Heuristiken (konfigurierbar) + Fallback."""
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_SCROLL", None)
        except Exception:
            cfg = None
        cfg_list = [x.strip().lower() for x in cfg.split(",") if x.strip()] if isinstance(cfg, str) else []
        KNOWN_BRIDGES = set(cfg_list)

        to_addr = tx.get("to") or ""
        if to_addr and to_addr.lower() in KNOWN_BRIDGES:
            return "bridge"

        selector = (tx.get("input") or "0x")[:10]
        try:
            from app.config import settings  # type: ignore
            known_selectors = getattr(settings, "BRIDGE_METHOD_SELECTORS", None)
        except Exception:
            known_selectors = None
        selector_set = set(known_selectors) if isinstance(known_selectors, (list, tuple, set)) else set()
        if selector and selector in selector_set:
            return "bridge"

        return super()._determine_event_type(tx, receipt)
