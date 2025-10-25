"""
Lightweight Preisservice für USD-Bewertungen ohne harte externe Abhängigkeiten.
- Nutzt optionale ENV-Overrides:
  - PRICE_OVERRIDES_JSON: z.B. {"ETH": 2500.0, "USDC": 1.0, "USDT": 1.0}
  - ETH_USD_PRICE: einfacher Fallback für ETH
- Enthält minimale Defaults: USDC/USDT = 1.0
- In-Memory Cache innerhalb des Prozesslaufs
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import os
import json
import time


class PriceService:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        # TTL in Sekunden für Cacheeinträge
        try:
            self._ttl = int(os.getenv("PRICE_CACHE_TTL", "60"))
        except Exception:
            self._ttl = 60

    def _now(self) -> float:
        return time.time()

    def _get_override_map(self) -> Dict[str, float]:
        raw = os.getenv("PRICE_OVERRIDES_JSON", "{}")
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                # symbol -> price
                return {str(k).upper(): float(v) for k, v in data.items()}
        except Exception:
            pass
        return {}

    async def get_usd_price(self, chain_id: str, token_address: Optional[str], symbol: Optional[str]) -> Optional[float]:
        sym = (symbol or "").upper().strip()
        if not sym and token_address:
            # Kein Symbol vorhanden: keine Schätzung
            return None

        # Cache-Key auf Symbolbasis (Address kann je Chain variieren)
        key = f"{chain_id}:{sym or token_address or 'unknown'}"
        cached = self._cache.get(key)
        if cached and self._now() - cached.get("ts", 0) < self._ttl:
            return cached.get("price")

        # 1) ENV Overrides
        overrides = self._get_override_map()
        if sym in overrides:
            price = overrides[sym]
            self._cache[key] = {"price": price, "ts": self._now()}
            return price

        # 2) Minimal Defaults
        if sym in ("USDC", "USDT"):
            price = 1.0
            self._cache[key] = {"price": price, "ts": self._now()}
            return price

        if sym == "ETH":
            try:
                price = float(os.getenv("ETH_USD_PRICE", "0"))
                if price > 0:
                    self._cache[key] = {"price": price, "ts": self._now()}
                    return price
            except Exception:
                pass

        # Keine Quelle verfügbar
        return None


price_service = PriceService()
