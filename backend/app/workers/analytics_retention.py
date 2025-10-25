import asyncio
import os
import logging
from datetime import timedelta
from app.db.postgres import postgres_client

logger = logging.getLogger(__name__)

class AnalyticsRetentionWorker:
    def __init__(self, interval_seconds: int = 3600):
        self._running = False
        self._interval = interval_seconds

    async def start(self):
        self._running = True
        logger.info("AnalyticsRetentionWorker started")
        while self._running:
            try:
                await self._run_once()
            except Exception as e:
                logger.error(f"Retention worker error: {e}")
            await asyncio.sleep(self._interval)

    async def _run_once(self):
        if not getattr(postgres_client, "pool", None):
            return
        try:
            days = int(os.getenv("ANALYTICS_RETENTION_DAYS", "365"))
        except Exception:
            days = 365
        if days <= 0:
            return
        async with postgres_client.acquire() as conn:
            q = """
            DELETE FROM web_events
            WHERE ts < NOW() - ($1::text || ' days')::interval
            """
            res = await conn.execute(q, str(days))
            logger.info(f"Analytics retention: {res}")

    def stop(self):
        self._running = False

_retention_worker: AnalyticsRetentionWorker | None = None

def start_analytics_retention(interval_seconds: int = 86400):
    global _retention_worker
    _retention_worker = AnalyticsRetentionWorker(interval_seconds=interval_seconds)
    return _retention_worker


def stop_analytics_retention():
    global _retention_worker
    if _retention_worker:
        _retention_worker.stop()
