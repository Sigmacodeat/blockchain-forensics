"""Gnosis Chain Adapter (xDAI) - EVM-kompatibel"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any

from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class GnosisAdapter(EthereumAdapter):
    """Gnosis (xDAI) blockchain adapter – EVM-kompatibel"""

    def __init__(self, rpc_url: Optional[str] = None):
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, "GNOSIS_RPC_URL", None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://gnosis")
        self._chain_name = "gnosis"
        logger.info(f"Initialized Gnosis adapter with RPC: {self.rpc_url}")

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """Gnosis-spezifische Bridge-Heuristiken (konfigurierbar) + Fallback."""
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_GNOSIS", None)
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
