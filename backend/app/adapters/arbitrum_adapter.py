"""Arbitrum Chain Adapter"""

import logging
from typing import Optional, Dict, Any
from .ethereum_adapter import EthereumAdapter

logger = logging.getLogger(__name__)


class ArbitrumAdapter(EthereumAdapter):
    """Arbitrum One blockchain adapter - Optimistic Rollup L2"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """Initialize Arbitrum adapter with Arbitrum-specific configuration"""
        if rpc_url is None:
            try:
                from app.config import settings  # type: ignore
                rpc_url = getattr(settings, 'ARBITRUM_RPC_URL', None)
            except Exception:
                rpc_url = None
        super().__init__(rpc_url or "mock://arbitrum")
        self._chain_name = "arbitrum"
        logger.info(f"Initialized Arbitrum adapter with RPC: {self.rpc_url}")
    
    @property
    def chain_name(self) -> str:
        """Return chain identifier"""
        return self._chain_name
    
    def _determine_event_type(self, tx: Dict[str, Any], receipt: Dict[str, Any]) -> str:
        """
        Determine transaction type with Arbitrum-specific bridge detection.
        
        Known Arbitrum bridges:
        - Arbitrum Gateway (Canonical Bridge)
        - Third-party bridges (Hop, Across, Synapse, etc.)
        """
        # Arbitrum-specific bridge contracts
        default_bridges = [
            # Arbitrum Gateway Router (L1)
            "0x72ce9c846789fdb6fc1f34ac4ad25dd9ef7031ef",
            # Arbitrum ERC20 Gateway
            "0xa3a7b6f88361f48403514059f1f16c8e78d60eec",
            # Arbitrum Custom Gateway
            "0xcee284f754e854890e311e3280b767f80797180d",
            # Popular third-party bridges
            "0x3666f603cc164936c1b87e207f36beba4ac5f18a",  # Hop Protocol
            "0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae",  # Synapse
        ]
        
        try:
            from app.config import settings  # type: ignore
            cfg = getattr(settings, "BRIDGE_CONTRACTS_ARBITRUM", None)
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
        
        # Arbitrum-specific: Check for retryable tickets (L1 -> L2 messages)
        # These have specific gas fields
        if tx.get('type') == 100 or tx.get('type') == '0x64':  # Arbitrum internal tx type
            return "bridge"
        
        # Fallback to parent implementation
        return super()._determine_event_type(tx, receipt)
