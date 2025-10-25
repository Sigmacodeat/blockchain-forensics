"""
Compliance screening service (dev): simple risk scoring and watchlist checks.
In production, replace with integrations (OFAC, TRM, Chainalysis) and stronger logic.
"""
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import re
import time
import os
from app.repos.compliance_repo import (
    add_watch as repo_add_watch,
    list_watch as repo_list_watch,
    list_watch_filtered as repo_list_watch_filtered,
    list_watch_page as repo_list_watch_page,
)


@dataclass
class ScreeningResult:
    chain: str
    address: str
    risk_score: int  # 0-100
    categories: List[str]
    reasons: List[str]
    watchlisted: bool


class ComplianceService:
    def __init__(self):
        # naive watchlist (lowercased)
        self._watchlist: Dict[str, Dict[str, Any]] = {
            "ethereum::0xdac17f958d2ee523a2206206994597c13d831ec7": {"reason": "High-volume token contract"},
            "ethereum::0x1111111254EEB25477B68fb85Ed929f73A960582".lower(): {"reason": "DEX Router"},
        }
        self._mixer_patterns = [
            re.compile(r"tornado", re.I),
        ]
        # simple in-memory cache: key -> (expires_at, ScreeningResult)
        self._cache: Dict[str, Tuple[float, ScreeningResult]] = {}
        self._ttl_seconds = int(os.getenv("COMPLIANCE_CACHE_TTL", "600"))  # 10 min default

    def _key(self, chain: str, address: str) -> str:
        return f"{chain.lower()}::{address.lower()}"

    def screen(self, chain: str, address: str) -> ScreeningResult:
        # cache lookup
        k = self._key(chain, address)
        now = time.time()
        ent = self._cache.get(k)
        if ent and ent[0] > now:
            return ent[1]
        reasons: List[str] = []
        categories: List[str] = []
        key = self._key(chain, address)
        watch = key in self._watchlist
        if watch:
            reasons.append(f"Watchlist: {self._watchlist[key].get('reason', 'listed')}")
            categories.append("watchlist")
        # naive heuristics
        if address.lower().startswith("0x0000000000"):
            reasons.append("Suspicious pattern: null-like address")
            categories.append("suspicious")
        for pat in self._mixer_patterns:
            if pat.search(address):
                reasons.append("Mixer pattern in address")
                categories.append("mixer")
                break
        # simple risk scoring
        base = 10
        if watch:
            base = 90
        if "mixer" in categories:
            base = max(base, 70)
        if "suspicious" in categories:
            base = max(base, 40)
        score = min(100, base)
        res = ScreeningResult(
            chain=chain,
            address=address,
            risk_score=score,
            categories=list(sorted(set(categories))),
            reasons=reasons,
            watchlisted=watch,
        )
        # store in cache
        self._cache[k] = (now + self._ttl_seconds, res)
        return res

    async def add_watch(self, chain: str, address: str, reason: str = "manual") -> Dict[str, Any]:
        # persist to Postgres repo
        return await repo_add_watch(chain, address, reason)

    async def list_watch(self) -> List[Dict[str, Any]]:
        return await repo_list_watch()

    async def list_watch_filtered(self, chain: str | None = None, address: str | None = None) -> List[Dict[str, Any]]:
        return await repo_list_watch_filtered(chain, address)

    async def list_watch_page(self, chain: str | None, address: str | None, limit: int, offset: int) -> Dict[str, Any]:
        return await repo_list_watch_page(chain, address, limit, offset)


service = ComplianceService()
