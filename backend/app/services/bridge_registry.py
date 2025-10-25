from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class BridgeContract:
    address: str
    chain: str
    name: str
    bridge_type: str
    counterpart_chains: List[str]
    method_selectors: List[str]
    added_at: datetime


class _BridgeRegistry:
    """
    Lightweight in-memory Bridge Registry used for tests and fallback runtime.
    Provides a minimal API consumed by tools:
    - is_bridge_method(selector)
    - is_bridge_contract(address, chain)
    - get_contract(address, chain)
    - get_contracts_by_chain(chain)
    - get_stats()
    """

    def __init__(self) -> None:
        self._contracts: Dict[str, List[BridgeContract]] = {}
        self._selectors: set[str] = set()
        self._init_sample()

    def _init_sample(self) -> None:
        now = datetime.utcnow()
        # Minimal sample data sufficient for tests
        samples = [
            BridgeContract(
                address="0x1111111111111111111111111111111111111111",
                chain="ethereum",
                name="Hop ETH Bridge",
                bridge_type="liquidity",
                counterpart_chains=["polygon", "arbitrum", "optimism"],
                method_selectors=["0xa9059cbb", "0x23b872dd"],  # transfer, transferFrom
                added_at=now,
            ),
            BridgeContract(
                address="0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",
                chain="polygon",
                name="Polygon PoS Bridge (ERC20 Predicate)",
                bridge_type="pos",
                counterpart_chains=["ethereum"],
                method_selectors=["0xa9059cbb"],
                added_at=now,
            ),
        ]
        for c in samples:
            self._contracts.setdefault(c.chain, []).append(c)
            self._selectors.update(c.method_selectors)

    # Public API
    def is_bridge_method(self, selector: str) -> bool:
        selector = (selector or "").lower()
        return selector in self._selectors

    def is_bridge_contract(self, address: str, chain: str) -> bool:
        address = (address or "").lower()
        chain = (chain or "").lower()
        return any(c.address.lower() == address for c in self._contracts.get(chain, []))

    def get_contract(self, address: str, chain: str) -> Optional[BridgeContract]:
        address = (address or "").lower()
        chain = (chain or "").lower()
        for c in self._contracts.get(chain, []):
            if c.address.lower() == address:
                return c
        return None

    def get_contracts_by_chain(self, chain: str) -> List[BridgeContract]:
        chain = (chain or "").lower()
        return list(self._contracts.get(chain, []))

    def get_stats(self) -> Dict[str, int]:
        total = sum(len(v) for v in self._contracts.values())
        return {
            "total_contracts": total,
            "chains": len(self._contracts),
            "selectors": len(self._selectors),
        }


bridge_registry = _BridgeRegistry()
