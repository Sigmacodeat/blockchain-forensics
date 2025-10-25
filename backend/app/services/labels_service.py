"""
Simple in-memory labels store for dev/testing.
Replace with persistent DB/service later.
"""
from typing import Dict, List
from dataclasses import dataclass, asdict
import threading


@dataclass
class Label:
    chain: str
    address: str
    label: str
    category: str = "generic"


class LabelsStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: Dict[str, List[Label]] = {}

    def _key(self, chain: str, address: str) -> str:
        return f"{chain.lower()}::{address.lower()}"

    def add(self, chain: str, address: str, label: str, category: str = "generic") -> Dict:
        with self._lock:
            key = self._key(chain, address)
            entry = Label(chain=chain, address=address, label=label, category=category)
            self._data.setdefault(key, []).append(entry)
            return asdict(entry)

    def get(self, chain: str, address: str) -> List[Dict]:
        key = self._key(chain, address)
        with self._lock:
            return [asdict(x) for x in self._data.get(key, [])]


store = LabelsStore()

# Seed with a few examples
store.add("ethereum", "0xdac17f958d2ee523a2206206994597c13d831ec7", "Tether USD (USDT)", category="token")
store.add("ethereum", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "Wrapped Ether (WETH)", category="token")
store.add("solana", "So11111111111111111111111111111111111111112", "Wrapped SOL", category="token")
