"""
News Feeds Update Worker
========================

Periodisch RSS/Atom News-Feeds abrufen, normalisieren und lokal persistieren.
Verwendet app.services.news_service.run_once().

Features:
- Konfigurierbares Intervall via NEWS_FEEDS_UPDATE_INTERVAL_MINUTES (Default 180)
- Robuste Fehlerbehandlung und einfache Prometheus-Metriken (falls vorhanden)
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

try:
    from app.metrics import (
        WORKER_STATUS,
        WORKER_PROCESSED_TOTAL,
        WORKER_ERRORS_TOTAL,
        WORKER_LAST_HEARTBEAT,
    )
except Exception:
    WORKER_STATUS = None  # type: ignore
    WORKER_PROCESSED_TOTAL = None  # type: ignore
    WORKER_ERRORS_TOTAL = None  # type: ignore
    WORKER_LAST_HEARTBEAT = None  # type: ignore

from app.services import news_service

logger = logging.getLogger(__name__)


class NewsFeedsUpdateWorker:
    def __init__(self) -> None:
        self.running: bool = False
        self.worker_name: str = "news_feeds_update"
        self.update_interval: timedelta = self._get_update_interval()
        self.last_update: Optional[datetime] = None

    def _get_update_interval(self) -> timedelta:
        try:
            minutes = int(os.getenv("NEWS_FEEDS_UPDATE_INTERVAL_MINUTES", "180"))
            return timedelta(minutes=minutes)
        except Exception:
            return timedelta(minutes=180)

    async def _heartbeat(self) -> None:
        try:
            if WORKER_LAST_HEARTBEAT is not None:
                WORKER_LAST_HEARTBEAT.labels(worker=self.worker_name).set(datetime.utcnow().timestamp())
        except Exception:
            pass

    async def _set_status(self, status: int) -> None:
        try:
            if WORKER_STATUS is not None:
                WORKER_STATUS.labels(worker=self.worker_name).set(status)
        except Exception:
            pass

    async def run_update_cycle(self) -> Dict[str, Any]:
        try:
            await self._heartbeat()
            logger.info("Starting news feeds update cycle")
            res = await news_service.run_once()
            try:
                if WORKER_PROCESSED_TOTAL is not None:
                    WORKER_PROCESSED_TOTAL.labels(worker=self.worker_name).inc()
            except Exception:
                pass
            self.last_update = datetime.utcnow()
            logger.info(f"News feeds update completed: {res}")
            return {"status": "success", **res}
        except Exception as e:
            logger.error(f"News feeds update cycle failed: {e}")
            try:
                if WORKER_ERRORS_TOTAL is not None:
                    WORKER_ERRORS_TOTAL.labels(worker=self.worker_name).inc()
            except Exception:
                pass
            return {"status": "error", "error": str(e)}

    async def run_loop(self) -> None:
        self.running = True
        await self._set_status(1)
        logger.info(f"Starting {self.worker_name} worker with interval: {self.update_interval}")
        try:
            while self.running:
                try:
                    if (self.last_update is None) or (datetime.utcnow() - self.last_update > self.update_interval):
                        result = await self.run_update_cycle()
                        if result.get("status") == "success":
                            await asyncio.sleep(self.update_interval.total_seconds())
                        else:
                            retry_delay = timedelta(minutes=15)
                            logger.info(f"News feeds update failed, retrying in {retry_delay}")
                            await asyncio.sleep(retry_delay.total_seconds())
                    else:
                        remaining = self.update_interval - (datetime.utcnow() - self.last_update)
                        wait_time = min(remaining.total_seconds(), 1800)
                        await asyncio.sleep(max(1.0, wait_time))
                except asyncio.CancelledError:
                    logger.info(f"{self.worker_name} worker cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in {self.worker_name} worker loop: {e}")
                    await asyncio.sleep(60)
        finally:
            await self._set_status(0)
            logger.info(f"{self.worker_name} worker stopped")

    def stop(self) -> None:
        logger.info(f"Stopping {self.worker_name} worker")
        self.running = False


news_feeds_worker = NewsFeedsUpdateWorker()


async def start_news_feeds_worker() -> None:
    await news_feeds_worker.run_loop()


def stop_news_feeds_worker() -> None:
    news_feeds_worker.stop()
