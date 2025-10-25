"""Celo Blockchain Adapter - EVM-compatible with mobile-first focus"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any
from app.adapters.ethereum_adapter import EthereumAdapter
from app.services.multi_chain import ChainInfo

logger = logging.getLogger(__name__)


class CeloAdapter(EthereumAdapter):
    """Celo blockchain adapter - EVM-compatible L1 for mobile payments"""
    
    def __init__(self, chain_info: Optional[ChainInfo] = None, rpc_url: Optional[str] = None):
        if chain_info is None:
            chain_info = ChainInfo(
                chain_id="celo",
                name="Celo",
                symbol="CELO",
                chain_type="evm",
                rpc_urls=[rpc_url] if rpc_url else ["https://forno.celo.org"],
                block_explorer_url="https://celoscan.io",
                native_currency={"name": "Celo", "symbol": "CELO", "decimals": 18},
                features=["mobile_payments", "stable_coins", "carbon_negative"]
            )
        self.chain_info = chain_info
        super().__init__(rpc_url=chain_info.rpc_urls[0] if chain_info.rpc_urls else rpc_url)
        self._chain_name = "celo"

    @property
    def chain_name(self) -> str:
        return self._chain_name

    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """Celo-spezifische Bridge-Heuristiken (konfigurierbar) + Fallback."""
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_CELO", None)
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

    async def initialize(self):
        logger.info(f"Initializing Celo adapter for {self.chain_info.name}")
