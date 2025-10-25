"""Base Chain Adapter"""

import logging
from typing import Optional, Dict, Any
from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class BaseAdapter(EthereumAdapter):
    """Base blockchain adapter - OP Stack L2 by Coinbase"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """Initialize Base adapter with Base-specific configuration"""
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, 'BASE_RPC_URL', None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://base")
        self._chain_name = "base"
        logger.info(f"Initialized Base adapter with RPC: {self.rpc_url}")
    
    @property
    def chain_name(self) -> str:
        """Return chain identifier"""
        return self._chain_name
    
    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """
        Determine transaction type with Base-specific bridge detection.
        
        Known Base bridges:
        - Base Gateway (Canonical Bridge, OP Stack)
        - Third-party bridges (Hop, Across, Stargate, etc.)
        """
        # Base-specific bridge contracts
        default_bridges = [
            # Base L1 Standard Bridge
            "0x3154cf16ccdb4c6d922629664174b904d80f2c35",
            # Base L1 Cross Domain Messenger
            "0x866e82a600a1414e583f7f13623f1ac5d58b0afa",
            # Base Portal (deposit contract)
            "0x49048044d57e1c92a77f79988d21fa8faf74e97e",
            # Popular third-party bridges
            "0x46290b0c3a234e3d538050d8f34421797532a827",  # Stargate
            "0xb8901acb165ed027e32754e0ffe830802919727f",  # Across
        ]
        
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_BASE", None)
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
        
        # Base uses OP Stack, so check for deposit transaction type
        if tx.get('type') == 126 or tx.get('type') == '0x7e':  # OP deposit tx type
            return "bridge"
        
        # Fallback to parent implementation
        return super()._determine_event_type(tx, receipt)
