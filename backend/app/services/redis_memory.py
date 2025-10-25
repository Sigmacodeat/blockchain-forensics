"""Chat memory service with Redis backend and in-memory fallback.

The legacy tests patch ``app.services.redis_memory.RedisMemory``.  This module
now provides a lightweight class with async helpers.  When Redis is unavailable
or under TEST_MODE the class stores messages in a process-local dictionary so
test-suites can operate deterministically without external services.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import defaultdict
from typing import Optional, List, Dict

from app.config import settings

logger = logging.getLogger(__name__)


class RedisMemory:
    """Small utility for chat memory with async interface."""

    _redis_client = None
    _memory_store: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    _lock = asyncio.Lock()

    @classmethod
    def _is_test_mode(cls) -> bool:
        return os.getenv("TEST_MODE") == "1" or getattr(settings, "TESTING", False)

    @classmethod
    def _get_client(cls):
        if cls._is_test_mode():
            if cls._redis_client is not None:
                try:
                    cls._redis_client.close()
                except Exception:
                    pass
                cls._redis_client = None
            return None

        if cls._redis_client is not None:
            return cls._redis_client

        try:
            import redis.asyncio as redis

            redis_url = getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
            cls._redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=float(getattr(settings, "REDIS_CONNECT_TIMEOUT", 0.5) or 0.5),
                socket_timeout=float(getattr(settings, "REDIS_SOCKET_TIMEOUT", 0.5) or 0.5),
            )
            logger.info("Redis memory client initialized: %s", redis_url)
        except Exception as exc:
            logger.warning("Redis not available, using in-memory chat memory: %s", exc)
            cls._redis_client = None
        return cls._redis_client

    @classmethod
    async def get_messages(cls, session_id: str, limit: int = 20) -> Optional[List[Dict[str, str]]]:
        if not session_id:
            return None

        client = cls._get_client()
        if client is None:
            async with cls._lock:
                messages = cls._memory_store.get(session_id, [])
                if not messages:
                    return None
                return messages[-limit:]

        try:
            key = f"chat:session:{session_id}"
            raw = await client.lrange(key, -limit, -1)
            messages = [json.loads(item) for item in raw if item]
            return messages or None
        except Exception as exc:
            logger.error("Failed to fetch chat memory (%s): %s", session_id, exc)
            return None

    @classmethod
    async def add_message(
        cls,
        session_id: str,
        role: str,
        content: str,
        ttl: int = 86400,
        max_messages: int = 30,
    ) -> None:
        if not session_id or not content:
            return

        payload = json.dumps({"role": role, "content": content})
        client = cls._get_client()
        if client is None:
            async with cls._lock:
                bucket = cls._memory_store[session_id]
                bucket.append({"role": role, "content": content})
                cls._memory_store[session_id] = bucket[-max_messages:]
            return

        try:
            key = f"chat:session:{session_id}"
            await client.rpush(key, payload)
            await client.ltrim(key, -max_messages, -1)
            await client.expire(key, ttl)
        except Exception as exc:
            logger.error("Failed to append chat memory (%s): %s", session_id, exc)

    @classmethod
    async def clear(cls, session_id: str) -> None:
        if not session_id:
            return

        client = cls._get_client()
        if client is None:
            async with cls._lock:
                cls._memory_store.pop(session_id, None)
            return

        try:
            key = f"chat:session:{session_id}"
            await client.delete(key)
        except Exception as exc:
            logger.error("Failed to clear chat memory (%s): %s", session_id, exc)


# Backwards compatible module-level helpers


async def get_chat_memory(session_id: str, limit: int = 20) -> Optional[List[Dict[str, str]]]:
    return await RedisMemory.get_messages(session_id, limit=limit)


async def append_chat_memory(
    session_id: str,
    role: str,
    content: str,
    ttl: int = 86400,
    max_messages: int = 30,
) -> None:
    await RedisMemory.add_message(session_id, role, content, ttl=ttl, max_messages=max_messages)


async def clear_chat_memory(session_id: str) -> None:
    await RedisMemory.clear(session_id)


def get_redis_client():
    try:
        return RedisMemory._get_client()
    except Exception:
        return None
