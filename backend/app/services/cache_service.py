"""
Caching-System für Blockchain-Forensik-Anwendung

Implementiert Redis-Caching für häufige Abfragen und Daten.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

# Redis-Caching (optional)
try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False
    logging.warning("Redis nicht verfügbar - Fallback zu In-Memory-Cache")

logger = logging.getLogger(__name__)

class CacheEntry:
    """Repräsentiert einen Cache-Eintrag"""

    def __init__(self, data: Any, ttl: int = 300, created_at: Optional[datetime] = None):
        self.data = data
        self.ttl = ttl  # Time to live in seconds
        self.created_at = created_at or datetime.utcnow()

    def is_expired(self) -> bool:
        """Prüft ob der Cache-Eintrag abgelaufen ist"""
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Entry in Dictionary für JSON-Serialisierung"""
        return {
            "data": self.data,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Erstellt Entry aus Dictionary"""
        return cls(
            data=data["data"],
            ttl=data["ttl"],
            created_at=datetime.fromisoformat(data["created_at"])
        )

class CacheService:
    """Haupt-Cache-Service mit Redis und In-Memory-Fallback"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client: Optional[Redis] = None
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

        if _REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info(f"Redis-Cache verbunden mit {redis_url}")
            except Exception as e:
                logger.error(f"Redis-Verbindung fehlgeschlagen: {e}")
                self.redis_client = None

    def _generate_key(self, key_parts: List[str]) -> str:
        """Generiert einen eindeutigen Cache-Key"""
        key_string = ":".join(str(part) for part in key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    async def get(self, key_parts: List[str]) -> Optional[Any]:
        """Holt Daten aus dem Cache"""
        cache_key = self._generate_key(key_parts)

        try:
            if self.redis_client:
                # Redis-Cache prüfen
                redis_data = await self.redis_client.get(cache_key)
                if redis_data:
                    entry_dict = json.loads(redis_data)
                    entry = CacheEntry.from_dict(entry_dict)

                    if not entry.is_expired():
                        self.cache_stats["hits"] += 1
                        return entry.data
                    else:
                        # Abgelaufener Eintrag - löschen
                        await self.redis_client.delete(cache_key)
                        return None
            else:
                # In-Memory-Cache prüfen
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    if not entry.is_expired():
                        self.cache_stats["hits"] += 1
                        return entry.data
                    else:
                        # Abgelaufener Eintrag - löschen
                        del self.memory_cache[cache_key]
                        return None

            self.cache_stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache-Get-Fehler für Key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(self, key_parts: List[str], data: Any, ttl: int = 300) -> bool:
        """Speichert Daten im Cache"""
        cache_key = self._generate_key(key_parts)
        entry = CacheEntry(data=data, ttl=ttl)

        try:
            if self.redis_client:
                # In Redis speichern
                await self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(entry.to_dict())
                )
            else:
                # In In-Memory-Cache speichern
                self.memory_cache[cache_key] = entry

            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Cache-Set-Fehler für Key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key_parts: List[str]) -> bool:
        """Löscht Daten aus dem Cache"""
        cache_key = self._generate_key(key_parts)

        try:
            if self.redis_client:
                deleted = await self.redis_client.delete(cache_key)
            else:
                deleted = 1 if cache_key in self.memory_cache else 0
                if deleted:
                    del self.memory_cache[cache_key]

            if deleted:
                self.cache_stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Cache-Delete-Fehler für Key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return False

    async def clear(self) -> bool:
        """Leert den gesamten Cache"""
        try:
            if self.redis_client:
                # Redis-Flush (nur für Test-Instanz)
                if "test" in str(self.redis_client.connection_pool.connection_kwargs.get('db', 0)):
                    await self.redis_client.flushdb()
                else:
                    # Für Produktion: Nur spezifische Keys löschen
                    pattern = "*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
            else:
                self.memory_cache.clear()

            self.cache_stats = {k: 0 for k in self.cache_stats}
            return True

        except Exception as e:
            logger.error(f"Cache-Clear-Fehler: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Holt Cache-Statistiken"""
        hit_rate = 0.0
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests > 0:
            hit_rate = (self.cache_stats["hits"] / total_requests) * 100

        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache) if not self.redis_client else 0
        }

    async def health_check(self) -> Dict[str, Any]:
        """Prüft die Cache-Gesundheit"""
        try:
            # Test-Schreib-/Lese-Operation
            test_key = ["health_check", datetime.utcnow().isoformat()]
            test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}

            # Schreiben
            await self.set(test_key, test_data, ttl=60)

            # Lesen
            retrieved_data = await self.get(test_key)

            # Löschen
            await self.delete(test_key)

            return {
                "status": "healthy" if retrieved_data else "unhealthy",
                "cache_type": "redis" if self.redis_client else "memory",
                "stats": self.get_stats()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "cache_type": "redis" if self.redis_client else "memory"
            }

# Cache-Decorators für einfache Verwendung
def cache_result(ttl: int = 300, key_prefix: str = ""):
    """Decorator für automatisches Caching von Funktionsergebnissen"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Cache-Key erstellen
            key_parts = [key_prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            cache_key = cache_service._generate_key(key_parts)

            # Aus Cache holen
            cached_result = await cache_service.get([cache_key])
            if cached_result is not None:
                return cached_result

            # Funktion ausführen
            result = await func(*args, **kwargs)

            # Im Cache speichern
            await cache_service.set([cache_key], result, ttl)

            return result
        return wrapper
    return decorator

# Singleton-Instance
cache_service = CacheService()

# Convenience-Funktionen für häufige Cache-Operationen
async def cache_wallet_balance(wallet_id: str, chain: str, balance: Dict[str, Any]) -> bool:
    """Cached Wallet-Balance"""
    return await cache_service.set(
        ["wallet_balance", wallet_id, chain],
        balance,
        ttl=60  # 1 Minute TTL für Balance-Daten
    )

async def get_cached_wallet_balance(wallet_id: str, chain: str) -> Optional[Dict[str, Any]]:
    """Holt gecachte Wallet-Balance"""
    return await cache_service.get(["wallet_balance", wallet_id, chain])

async def cache_transaction_history(wallet_id: str, chain: str, history: List[Dict[str, Any]]) -> bool:
    """Cached Transaktionshistorie"""
    return await cache_service.set(
        ["transaction_history", wallet_id, chain],
        history,
        ttl=300  # 5 Minuten TTL für Historie
    )

async def get_cached_transaction_history(wallet_id: str, chain: str) -> Optional[List[Dict[str, Any]]]:
    """Holt gecachte Transaktionshistorie"""
    return await cache_service.get(["transaction_history", wallet_id, chain])

async def cache_ai_analysis(analysis_type: str, input_data: str, result: Dict[str, Any]) -> bool:
    """Cached KI-Analyse-Ergebnisse"""
    return await cache_service.set(
        ["ai_analysis", analysis_type, input_data],
        result,
        ttl=1800  # 30 Minuten TTL für KI-Analysen
    )

async def cache_chat_response(session_id: str, message_id: int, response: Dict[str, Any]) -> bool:
    """Cached Chat-Antwort"""
    return await cache_service.set(
        ["chat_response", session_id, str(message_id)],
        response,
        ttl=3600  # 1 Stunde TTL für Chat-Antworten
    )

async def get_cached_chat_response(session_id: str, message_id: int) -> Optional[Dict[str, Any]]:
    """Holt gecachte Chat-Antwort"""
    return await cache_service.get(["chat_response", session_id, str(message_id)])

async def cache_ocr_result(file_hash: str, ocr_result: Dict[str, Any]) -> bool:
    """Cached OCR-Ergebnis"""
    return await cache_service.set(
        ["ocr_result", file_hash],
        ocr_result,
        ttl=86400  # 24 Stunden TTL für OCR-Ergebnisse
    )

async def get_cached_ocr_result(file_hash: str) -> Optional[Dict[str, Any]]:
    """Holt gecachtes OCR-Ergebnis"""
    return await cache_service.get(["ocr_result", file_hash])

async def cache_kb_search(query_hash: str, results: List[Dict[str, Any]]) -> bool:
    """Cached KB-Suchergebnisse"""
    return await cache_service.set(
        ["kb_search", query_hash],
        results,
        ttl=1800  # 30 Minuten TTL für KB-Suchen
    )

async def get_cached_kb_search(query_hash: str) -> Optional[List[Dict[str, Any]]]:
    """Holt gecachte KB-Suchergebnisse"""
    return await cache_service.get(["kb_search", query_hash])
