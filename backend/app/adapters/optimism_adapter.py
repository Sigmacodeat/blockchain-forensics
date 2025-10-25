"""Optimism Chain Adapter"""

import logging
from typing import Optional, Dict, Any
from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class OptimismAdapter(EthereumAdapter):
    """Optimism blockchain adapter - Optimistic Rollup L2"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """Initialize Optimism adapter with Optimism-specific configuration"""
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, 'OPTIMISM_RPC_URL', None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://optimism")
        self._chain_name = "optimism"
        logger.info(f"Initialized Optimism adapter with RPC: {self.rpc_url}")
    
    @property
    def chain_name(self) -> str:
        """Return chain identifier"""
        return self._chain_name
    
    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """
        Determine transaction type with Optimism-specific bridge detection.
        
        Known Optimism bridges:
        - Optimism Gateway (Canonical Bridge)
        - Third-party bridges (Hop, Across, Synapse, etc.)
        """
        # Optimism-specific bridge contracts
        default_bridges = [
            # Optimism L1 Standard Bridge
            "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1",
            # Optimism L1 Cross Domain Messenger
            "0x25ace71c97b33cc4729cf772ae268934f7ab5fa1",
            # Optimism Gateway
            "0x735adbbe72226bd52e818e7181953f42e3b0ff21",
            # Popular third-party bridges
            "0x83f6244bd87662118d96d9a6d44f09dfff14b30e",  # Hop Protocol
            "0xaf41a65f362ca6a4e6f8e0f7e6b5c29e4f0e6c34",  # Synapse
        ]
        
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_OPTIMISM", None)
        except Exception:
            cfg = None
        cfg_list = [x.strip().lower() for x in cfg.split(",") if x.strip()] if isinstance(cfg, str) else []
        KNOWN_BRIDGES = set([a.lower() for a in (cfg_list or default_bridges)])
        
        to_addr = tx.get('to') or ''
        if to_addr and to_addr.lower() in KNOWN_BRIDGES:
            return "bridge"
        
        # Check method selectors
        selector = (tx.get('input') or '0x')[:10]
        try:
            from app.config import settings  # type: ignore
            known_selectors = getattr(settings, "BRIDGE_METHOD_SELECTORS", None)
        except Exception:
            known_selectors = None
        selector_set = set(known_selectors) if isinstance(known_selectors, (list, tuple, set)) else set()
        if selector and selector in selector_set:
            return "bridge"
        
        # Optimism-specific: Check for deposit transactions (L1 -> L2)
        # These typically have a specific gas pattern and type
        if tx.get('type') == 126 or tx.get('type') == '0x7e':  # OP deposit tx type
            return "bridge"
        
        # Fallback to parent implementation
        return super()._determine_event_type(tx, receipt)
