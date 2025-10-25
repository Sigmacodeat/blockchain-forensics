"""
Simple JSON-RPC helper using standard library only (no extra deps).
Provides async-friendly wrappers via asyncio.to_thread.
"""
from __future__ import annotations

import base64
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple
import asyncio
import time
import os
import hashlib
try:
    import redis.asyncio as redis
    _redis_module: ModuleType | None = redis  # runtime module
except Exception:  # pragma: no cover
    _redis_module = None

from app.config import settings
from types import ModuleType
from app.observability.metrics import JSONRPC_CACHE_HITS, JSONRPC_CACHE_MISSES, REDIS_UP


def _post(url: str, data: Dict[str, Any], auth: Optional[Dict[str, str]] = None, timeout: int = 20) -> Dict[str, Any]:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    if auth and auth.get("basic"):
        req.add_header("Authorization", f"Basic {auth['basic']}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error: {e}")


_CACHE: Dict[Tuple[str, str, str], Tuple[float, Dict[str, Any]]] = {}
_DEFAULT_TTL = 30.0  # seconds
from typing import Any as _Any
_REDIS_CLIENT: Optional[_Any] = None
_CACHE_NAMESPACE = getattr(settings, "JSONRPC_CACHE_NAMESPACE", "cf")


async def _get_redis() -> Optional[_Any]:
    global _REDIS_CLIENT
    url = getattr(settings, "REDIS_URL", "") or os.getenv("REDIS_URL", "")
    if not url or _redis_module is None:
        return None
    if _REDIS_CLIENT is None:
        try:
            from typing import cast
            _client_mod = cast(_Any, _redis_module)
            _REDIS_CLIENT = _client_mod.from_url(url, decode_responses=True)
            try:
                # ping to verify connectivity
                async def _ping() -> None:
                    try:
                        if _REDIS_CLIENT is not None:
                            from typing import Awaitable, cast
                            await cast(Awaitable[_Any], _REDIS_CLIENT.ping())
                            REDIS_UP.set(1)
                        else:
                            REDIS_UP.set(0)
                    except Exception:
                        REDIS_UP.set(0)
                # schedule immediate ping (callers are already async)
                await _ping()
            except Exception:
                try:
                    REDIS_UP.set(0)
                except Exception:
                    pass
        except Exception:
            _REDIS_CLIENT = None
            try:
                REDIS_UP.set(0)
            except Exception:
                pass
    return _REDIS_CLIENT


async def json_rpc(url: str, method: str, params: Any, auth_user: Optional[str] = None, auth_pass: Optional[str] = None, timeout: int = 20, no_cache: bool = False, ttl: float = _DEFAULT_TTL) -> Dict[str, Any]:
    auth = None
    if auth_user is not None and auth_pass is not None:
        token = base64.b64encode(f"{auth_user}:{auth_pass}".encode("utf-8")).decode("ascii")
        auth = {"basic": token}
    data = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}

    # cache key uses json-dumped params for stability (hash to keep key short)
    key_json = json.dumps(params, sort_keys=True)
    key: Tuple[str, str, str] = (url, method, key_json)
    key_hash = hashlib.sha1(f"{url}|{method}|{key_json}".encode("utf-8")).hexdigest()
    redis_key = f"{_CACHE_NAMESPACE}:jsonrpc:{method}:{key_hash}"
    now = time.time()
    if not no_cache:
        # Try Redis first
        client = await _get_redis()
        if client is not None:
            try:
                cached = await client.get(redis_key)
                if cached:
                    JSONRPC_CACHE_HITS.labels(layer="redis").inc()
                    return json.loads(cached)
            except Exception:
                pass
        # Fallback to in-memory
        hit = _CACHE.get(key)
        if hit and now - hit[0] <= ttl:
            JSONRPC_CACHE_HITS.labels(layer="memory").inc()
            return hit[1]
        else:
            JSONRPC_CACHE_MISSES.labels(layer="memory").inc()

    resp = await asyncio.to_thread(_post, url, data, auth, timeout)
    if not no_cache:
        # Set Redis
        client = await _get_redis()
        if client is not None:
            try:
                await client.setex(redis_key, int(ttl), json.dumps(resp))
                # count as miss resolved via redis set
                JSONRPC_CACHE_MISSES.labels(layer="redis").inc()
            except Exception:
                pass
        # Set in-memory fallback
        _CACHE[key] = (now, resp)
    return resp


async def json_rpc_invalidate(url: str, method: str, params: Any) -> None:
    """Invalidate a cached JSON-RPC response for given url/method/params.

    Removes both Redis and in-memory cache entries.
    """
    key_json = json.dumps(params, sort_keys=True)
    key: Tuple[str, str, str] = (url, method, key_json)
    _CACHE.pop(key, None)
    client = await _get_redis()
    if client is not None:
        try:
            key_hash = hashlib.sha1(f"{url}|{method}|{key_json}".encode("utf-8")).hexdigest()
            redis_key = f"{_CACHE_NAMESPACE}:jsonrpc:{method}:{key_hash}"
            await client.delete(redis_key)
        except Exception:
            pass


async def json_rpc_cache_set(url: str, method: str, params: Any, response: Dict[str, Any], ttl: float = _DEFAULT_TTL) -> None:
    """Manually prime the cache with a response (Redis + memory)."""
    now = time.time()
    key_json = json.dumps(params, sort_keys=True)
    key: Tuple[str, str, str] = (url, method, key_json)
    _CACHE[key] = (now, response)
    client = await _get_redis()
    if client is not None:
        try:
            key_hash = hashlib.sha1(f"{url}|{method}|{key_json}".encode("utf-8")).hexdigest()
            redis_key = f"{_CACHE_NAMESPACE}:jsonrpc:{method}:{key_hash}"
            await client.setex(redis_key, int(ttl), json.dumps(response))
        except Exception:
            pass
