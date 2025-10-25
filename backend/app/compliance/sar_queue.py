from __future__ import annotations
from typing import Dict, Optional
from datetime import datetime
import json
import logging

from app.db.redis_client import redis_client


logger = logging.getLogger(__name__)


class SARQueue:
    SAR_PREFIX = "sar:"
    
    def __init__(self) -> None:
        self._redis = redis_client
    
    async def enqueue(self, report_id: str, case_id: str, format: str) -> None:
        key = f"{self.SAR_PREFIX}{report_id}"
        data = {
            "report_id": report_id,
            "case_id": case_id,
            "format": format,
            "state": "queued",
            "updated_at": datetime.utcnow().isoformat(),
        }
        await self._redis.cache_set(key, data, ttl=86400 * 7)  # 7 days
        logger.info(f"SAR report {report_id} enqueued")
    
    async def set_status(self, report_id: str, state: str, details: Optional[Dict] = None) -> None:
        key = f"{self.SAR_PREFIX}{report_id}"
        existing = await self._redis.cache_get(key)
        if not existing:
            existing = {
                "report_id": report_id,
                "state": "unknown",
            }
        existing["state"] = state
        existing["updated_at"] = datetime.utcnow().isoformat()
        if details:
            existing["details"] = details
        await self._redis.cache_set(key, existing, ttl=86400 * 7)
        logger.info(f"SAR report {report_id} status set to {state}")
    
    async def get_status(self, report_id: str) -> Optional[Dict]:
        key = f"{self.SAR_PREFIX}{report_id}"
        return await self._redis.cache_get(key)
    
    async def all(self) -> Dict[str, Dict]:
        # Use scan to get all SAR keys
        results = {}
        client = self._redis.client
        if client is None:
            return results
        cursor = 0
        pattern = f"{self.SAR_PREFIX}*"
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                values = await client.mget(keys)
                for k, v in zip(keys, values):
                    try:
                        report_id = k.replace(self.SAR_PREFIX, "", 1)
                        results[report_id] = json.loads(v) if v else {}
                    except Exception:
                        continue
            if cursor == 0:
                break
        return results


sar_queue = SARQueue()
