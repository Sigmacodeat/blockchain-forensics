"""Binance Smart Chain (BSC) Adapter - EVM-kompatibel"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any

from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class BscAdapter(EthereumAdapter):
    """BSC blockchain adapter – baut auf dem generischen EthereumAdapter auf"""

    def __init__(self, rpc_url: Optional[str] = None):
        """Initialisiert den BSC-Adapter mit BSC-spezifischer Konfiguration.
        Bevorzugt Umgebungsvariable BSC_RPC_URL; fällt ansonsten auf bekannte Public RPCs zurück.
        """
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, "BSC_RPC_URL", None)
            except Exception:
                rpc_url = None
        # Fallback-Endpoint nur als Platzhalter, produktiv sollte über ENV konfiguriert werden
        super().__init__(rpc_url or "mock://bsc")
        self._chain_name = "bsc"
        logger.info(f"Initialized BSC adapter with RPC: {self.rpc_url}")

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """Optional: BSC-spezifische Bridge-Erkennung (über Settings konfigurierbar).
        Fällt auf generische EVM-Logik des Elternadapters zurück, wenn nichts passt.
        """
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_BSC", None)
        except Exception:
            cfg = None
        cfg_list = [x.strip().lower() for x in cfg.split(",") if x.strip()] if isinstance(cfg, str) else []
        KNOWN_BRIDGES = set(cfg_list)

        to_addr = tx.get("to") or ""
        if to_addr and to_addr.lower() in KNOWN_BRIDGES:
            return "bridge"

        # Optional: Methode-Selektoren aus globaler Konfiguration
        selector = (tx.get("input") or "0x")[:10]
        try:
            from app.config import settings  # type: ignore
            known_selectors = getattr(settings, "BRIDGE_METHOD_SELECTORS", None)
        except Exception:
            known_selectors = None
        selector_set = set(known_selectors) if isinstance(known_selectors, (list, tuple, set)) else set()
        if selector and selector in selector_set:
            return "bridge"

        # Fallback zur Standard-EVM-Logik (ERC20/NFT/DEX heuristics etc.)
        return super()._determine_event_type(tx, receipt)
