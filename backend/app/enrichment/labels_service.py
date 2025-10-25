"""Address Labeling and Enrichment Service"""

import logging
import csv
from typing import Optional, List, Dict, Set, Awaitable, cast, Any
from datetime import datetime, timedelta
import httpx
try:
    from redis.asyncio.client import Redis as AsyncRedis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore
    _REDIS_AVAILABLE = False
from cachetools import TTLCache  # type: ignore[import-untyped]

from app.config import settings

logger = logging.getLogger(__name__)


class LabelsService:
    """
    Address labeling service with OFAC sanctions, known entities, and ML classification.
    Integrates multiple data sources for comprehensive address intelligence.
    """
    
    def __init__(self):
        # Broad typing to avoid NameError when redis is not installed
        self.redis_client: Optional[Any] = None
        self.local_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour TTL
        
        # Known labels (loaded from various sources)
        self.sanctions_list: Set[str] = set()
        self.exchange_addresses: Dict[str, str] = {}
        self.scam_addresses: Set[str] = set()
        
        # Last update timestamps
        self.last_sanctions_update: Optional[datetime] = None
        
    async def initialize(self):
        """Initialize service and load data"""
        # Connect to Redis if available and not in TEST_MODE
        try:
            if not settings.TEST_MODE and _REDIS_AVAILABLE and AsyncRedis is not None:
                self.redis_client = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[attr-defined]
        except Exception:
            self.redis_client = None
        
        # Load sanctions list
        await self.update_sanctions_list()
        
        # Load known exchanges (sample data)
        self._load_known_exchanges()
        
        logger.info("Labels service initialized")
    
    async def update_sanctions_list(self, force: bool = False):
        """Update OFAC sanctions list"""
        # Check if update needed
        if not force and self.last_sanctions_update:
            if datetime.utcnow() - self.last_sanctions_update < timedelta(days=1):
                logger.info("Sanctions list is up to date")
                return

        # Skip network in TEST/OFFLINE
        try:
            import os
            if os.getenv("TEST_MODE") == "1" or os.getenv("OFFLINE_MODE") == "1":
                logger.info("Skipping sanctions fetch due to TEST/OFFLINE mode")
                return
        except Exception:
            pass

        try:
            logger.info("Downloading OFAC sanctions list...")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(settings.OFAC_SANCTIONS_URL, timeout=30)
                response.raise_for_status()
                
                # Parse CSV
                csv_data = csv.DictReader(response.text.splitlines())
                
                sanctioned_addresses = set()
                for row in csv_data:
                    # Extract crypto addresses from remarks/alt_id fields
                    address = row.get('Digital Currency Address', '').strip()
                    if address and address.startswith('0x'):
                        sanctioned_addresses.add(address.lower())
                
                self.sanctions_list = sanctioned_addresses
                self.last_sanctions_update = datetime.utcnow()
                
                logger.info(f"Loaded {len(sanctioned_addresses)} sanctioned addresses")
                
        except Exception as e:
            logger.error(f"Error updating sanctions list: {e}")
    
    def _load_known_exchanges(self):
        """Load known exchange addresses (sample data)"""
        # In production, load from database or external API
        self.exchange_addresses = {
            "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
            "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Cold Wallet",
            "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance Pool",
            "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance Staking",
            # Add more...
        }
    
    async def get_labels(self, address: str) -> List[str]:
        """
        Get all labels for an address
        
        Returns:
            List of labels like ['exchange', 'binance', 'hot_wallet']
        """
        address = address.lower()
        labels: List[str] = []
        
        # Check cache
        cache_key = f"labels:{address}"
        cached = self.local_cache.get(cache_key)
        if cached:
            return cached
        
        # Check Redis cache
        if self.redis_client:
            r = self.redis_client
            try:
                redis_labels = await cast(Awaitable[Set[str]], r.smembers(cache_key))
            except Exception:
                redis_labels = set()
            if redis_labels:
                labels = list(redis_labels)
                self.local_cache[cache_key] = labels
                return labels
        
        # Multi-Sanctions Aggregator (preferred)
        try:
            from app.compliance.sanctions.service import sanctions_service as _sanctions_service
            sres = _sanctions_service.screen(address=address)
            if bool(sres.get("matched")):
                labels.extend(["sanctioned"])  # canonical tag
                for src in (sres.get("lists") or []):
                    try:
                        if isinstance(src, str) and src:
                            labels.append(src.lower())
                    except Exception:
                        pass
        except Exception:
            # Fallback to simple OFAC list if aggregator unavailable
            if address in self.sanctions_list:
                labels.append("sanctioned")
                labels.append("ofac")
        
        # Check exchanges
        if address in self.exchange_addresses:
            labels.append("exchange")
            exchange_name = self.exchange_addresses[address]
            if "binance" in exchange_name.lower():
                labels.append("binance")
            if "hot wallet" in exchange_name.lower():
                labels.append("hot_wallet")
            elif "cold wallet" in exchange_name.lower():
                labels.append("cold_wallet")
        
        # Check scams
        if address in self.scam_addresses:
            labels.append("scam")
            labels.append("high_risk")
        
        # Dedupe before caching
        if labels:
            try:
                labels = list(dict.fromkeys(labels))
            except Exception:
                labels = list(set(labels))

        # Cache results
        self.local_cache[cache_key] = labels
        if self.redis_client and labels:
            r = self.redis_client
            try:
                if labels:
                    await cast(Awaitable[int], r.sadd(cache_key, *labels))
                await cast(Awaitable[bool], r.expire(cache_key, 3600))
            except Exception:
                pass

        return labels
    
    async def get_category(self, address: str) -> Optional[str]:
        """
        Get primary category for address
        
        Returns:
            'exchange', 'sanctioned', 'scam', 'contract', 'unknown'
        """
        labels = await self.get_labels(address)
        
        # Priority order
        if "sanctioned" in labels:
            return "sanctioned"
        if "scam" in labels:
            return "scam"
        if "exchange" in labels:
            return "exchange"
        
        return None
    
    async def is_high_risk(self, address: str) -> bool:
        """Check if address is high risk"""
        labels = await self.get_labels(address)
        high_risk_labels = {"sanctioned", "scam", "high_risk", "mixer", "darknet"}
        return bool(set(labels) & high_risk_labels)
    
    async def add_label(
        self,
        address: str,
        label: str,
        source: str = "manual",
        confidence: float = 1.0
    ):
        """Add custom label to address"""
        address = address.lower()

        # Add to cache
        cache_key = f"labels:{address}"
        if cache_key in self.local_cache:
            self.local_cache[cache_key].append(label)

        # Add to Redis
        if self.redis_client:
            r = self.redis_client
            try:
                await cast(Awaitable[int], r.sadd(cache_key, label))
            except Exception:
                pass
            
            # Store metadata
            meta_key = f"label_meta:{address}:{label}"
            try:
                await cast(Awaitable[int], r.hset(meta_key, mapping={
                    "source": source,
                    "confidence": str(confidence),
                    "added_at": datetime.utcnow().isoformat()
                }))
            except Exception:
                pass
        
        logger.info(f"Added label '{label}' to {address} (source: {source})")
    
    async def bulk_get_labels(self, addresses: List[str]) -> Dict[str, List[str]]:
        """Get labels for multiple addresses efficiently"""
        result: Dict[str, List[str]] = {}
        addrs = [a.lower() for a in addresses]
        # Try local cache first
        missing: List[str] = []
        for addr in addrs:
            cache_key = f"labels:{addr}"
            cached = self.local_cache.get(cache_key)
            if cached is not None:
                result[addr] = cached
            else:
                missing.append(addr)

        # Batch from Redis if available
        if self.redis_client and missing:
            try:
                pipe = self.redis_client.pipeline()
                keys = [f"labels:{m}" for m in missing]
                for k in keys:
                    pipe.smembers(k)
                res = await cast(Awaitable[List[Set[str]]], pipe.execute())
                for addr, members in zip(missing, res):
                    if members:
                        vals = list(members)
                        result[addr] = vals
                        self.local_cache[f"labels:{addr}"] = vals
            except Exception:
                pass

        # Fallback per-address for unresolved
        for addr in addrs:
            if addr not in result:
                result[addr] = await self.get_labels(addr)

        return result

    async def get_labels_detailed(self, address: str) -> List[Dict[str, str]]:
        """Return labels with source and confidence if available"""
        out: List[Dict[str, str]] = []
        labels = await self.get_labels(address)
        if not labels:
            return out
        if not self.redis_client:
            return [{"label": l, "source": "cache", "confidence": "1.0"} for l in labels]
        addr = address.lower()
        r = self.redis_client
        for l in labels:
            mk = f"label_meta:{addr}:{l}"
            try:
                meta = await cast(Awaitable[Dict[str, str]], r.hgetall(mk))
            except Exception:
                meta = {}
            out.append({
                "label": l,
                "source": meta.get("source", "cache"),
                "confidence": meta.get("confidence", "1.0"),
            })
        return out

    async def invalidate_cache(self, address: str) -> None:
        addr = address.lower()
        cache_key = f"labels:{addr}"
        if cache_key in self.local_cache:
            try:
                del self.local_cache[cache_key]
            except Exception:
                pass
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception:
                pass
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()


# Singleton instance
labels_service = LabelsService()
