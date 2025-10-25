"""Polygon Chain Adapter"""

import logging
from typing import Optional, Dict, Any
from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class PolygonAdapter(EthereumAdapter):
    """Polygon (Matic) blockchain adapter - EVM-compatible L2"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """Initialize Polygon adapter with Polygon-specific configuration"""
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, 'POLYGON_RPC_URL', None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://polygon")
        self._chain_name = "polygon"
        logger.info(f"Initialized Polygon adapter with RPC: {self.rpc_url}")
    
    @property
    def chain_name(self) -> str:
        """Return chain identifier"""
        return self._chain_name
    
    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """
        Determine transaction type with Polygon-specific bridge detection.
        
        Known Polygon bridges:
        - Polygon PoS Bridge (0x...)
        - Polygon zkEVM Bridge
        - Third-party bridges (Hop, Connext, etc.)
        """
        # Polygon-specific bridge contracts
        default_bridges = [
            # Polygon PoS Bridge (Plasma/PoS)
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77",  # RootChainManager
            "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",  # Polygon ERC20 Predicate
            # Polygon zkEVM Bridge
            "0x2a3dd3eb832af982ec71669e178424b10dca2ede",
            # Popular third-party bridges
            "0x4c4bd8a8e5e5dcf8d7c7c1c9e5e5e5e5e5e5e5e5",  # Placeholder for Hop
        ]
        
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_POLYGON", None)
        except Exception:
            cfg = None
        cfg_list = [x.strip().lower() for x in cfg.split(",") if x.strip()] if isinstance(cfg, str) else []
        KNOWN_BRIDGES = set([a.lower() for a in (cfg_list or default_bridges)])
        
        to_addr = tx.get('to') or ''
        if to_addr and to_addr.lower() in KNOWN_BRIDGES:
            return "bridge"
        
        # Check method selectors (same as parent for now)
        selector = (tx.get('input') or '0x')[:10]
        try:
            from app.config import settings  # type: ignore
            known_selectors = getattr(settings, "BRIDGE_METHOD_SELECTORS", None)
        except Exception:
            known_selectors = None
        selector_set = set(known_selectors) if isinstance(known_selectors, (list, tuple, set)) else set()
        if selector and selector in selector_set:
            return "bridge"
        
        # Fallback to parent implementation
        return super()._determine_event_type(tx, receipt)
