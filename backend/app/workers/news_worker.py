"""
News Feeds Update Worker
========================

Periodischer Worker, der die konfigurierten News-Quellen (RSS/Atom) abruft
und in data/news_feeds/news.json ablegt. Nutzt app.services.news_service.run_once().

ENV:
- ENABLE_NEWS_FEEDS_WORKER=1 (main.py startet Worker)
- NEWS_FEEDS_UPDATE_INTERVAL_MINUTES=120
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class NewsFeedsUpdateWorker:
    def __init__(self) -> None:
        self.running: bool = False
        self.worker_name: str = "news_feeds_update"
        self.update_interval: timedelta = self._get_update_interval()
        self.last_update: Optional[datetime] = None

    def _get_update_interval(self) -> timedelta:
        try:
            minutes = int(os.getenv("NEWS_FEEDS_UPDATE_INTERVAL_MINUTES", "120"))
            return timedelta(minutes=minutes)
        except Exception:
            return timedelta(minutes=120)

    async def run_update_cycle(self) -> Dict[str, Any]:
        try:
            logger.info("Starting news feeds update cycle")
            from app.services import news_service
            res = await news_service.run_once()
            self.last_update = datetime.utcnow()
            logger.info(f"News feeds update completed: {res}")
            return {"status": "success", **res}
        except Exception as e:
            logger.error(f"News feeds update failed: {e}")
            return {"status": "error", "error": str(e)}

    async def run_loop(self) -> None:
        self.running = True
        logger.info(f"Starting {self.worker_name} worker with interval: {self.update_interval}")
        try:
            while self.running:
                try:
                    if (self.last_update is None or datetime.utcnow() - self.last_update > self.update_interval):
                        res = await self.run_update_cycle()
                        if res.get("status") == "success":
                            await asyncio.sleep(self.update_interval.total_seconds())
                        else:
                            await asyncio.sleep(15 * 60)  # retry in 15m
                    else:
                        remaining = self.update_interval - (datetime.utcnow() - self.last_update)
                        await asyncio.sleep(max(1.0, min(remaining.total_seconds(), 1800)))
                except asyncio.CancelledError:
                    logger.info(f"{self.worker_name} worker cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in {self.worker_name} loop: {e}")
                    await asyncio.sleep(60)
        finally:
            logger.info(f"{self.worker_name} worker stopped")

    def stop(self) -> None:
        self.running = False


news_feeds_worker = NewsFeedsUpdateWorker()


async def start_news_feeds_worker() -> None:
    await news_feeds_worker.run_loop()


def stop_news_feeds_worker() -> None:
    news_feeds_worker.stop()
