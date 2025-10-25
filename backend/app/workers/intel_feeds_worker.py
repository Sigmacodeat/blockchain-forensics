"""
Intel Feeds Update Worker
=========================

Background worker that periodically fetches public intelligence feeds
and stores normalized items into the labels DB via bulk_upsert().
Uses app.intel.feeds.run_once().

Features:
- Configurable refresh interval via INTEL_FEEDS_UPDATE_INTERVAL_MINUTES (default 180)
- Error handling and worker metrics
- Best-effort, safe to run without DB (no-op save)
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.metrics import (
    WORKER_STATUS,
    WORKER_PROCESSED_TOTAL,
    WORKER_ERRORS_TOTAL,
    WORKER_LAST_HEARTBEAT,
)

logger = logging.getLogger(__name__)


class IntelFeedsUpdateWorker:
    def __init__(self) -> None:
        self.running: bool = False
        self.worker_name: str = "intel_feeds_update"
        self.update_interval: timedelta = self._get_update_interval()
        self.last_update: Optional[datetime] = None

    def _get_update_interval(self) -> timedelta:
        try:
            minutes = int(os.getenv("INTEL_FEEDS_UPDATE_INTERVAL_MINUTES", "180"))
            return timedelta(minutes=minutes)
        except Exception:
            return timedelta(minutes=180)

    async def _heartbeat(self) -> None:
        try:
            WORKER_LAST_HEARTBEAT.labels(worker=self.worker_name).set(datetime.utcnow().timestamp())
        except Exception:
            pass

    async def _set_status(self, status: int) -> None:
        try:
            WORKER_STATUS.labels(worker=self.worker_name).set(status)
        except Exception:
            pass

    async def run_update_cycle(self) -> Dict[str, Any]:
        """Run a single feeds ingestion cycle (intel feeds + label feeds aggregator)"""
        try:
            await self._heartbeat()
            logger.info("Starting intel feeds update cycle")

            intel_result: Dict[str, Any] = {}
            try:
                from app.intel import feeds as intel_feeds
                try:
                    intel_result = await intel_feeds.run_once()
                except Exception as e:
                    logger.error(f"Intel feeds run_once failed: {e}")
                    try:
                        WORKER_ERRORS_TOTAL.labels(worker=self.worker_name).inc()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Intel feeds module not available: {e}")

            label_feeds_result: Dict[str, Any] = {}
            try:
                from app.ingest.label_feeds_aggregator import aggregate_label_feeds
                label_feeds_result = await aggregate_label_feeds()
            except Exception as e:
                logger.error(f"Label feeds aggregation failed: {e}")
                try:
                    WORKER_ERRORS_TOTAL.labels(worker=self.worker_name).inc()
                except Exception:
                    pass

            try:
                WORKER_PROCESSED_TOTAL.labels(worker=self.worker_name).inc()
            except Exception:
                pass
            self.last_update = datetime.utcnow()

            combined = {"intel_feeds": intel_result, "label_feeds": label_feeds_result}
            logger.info(f"Intel feeds update completed: {combined}")
            return {"status": "success", **combined}
        except Exception as e:
            logger.error(f"Intel feeds update cycle failed: {e}")
            try:
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
                    if (self.last_update is None or datetime.utcnow() - self.last_update > self.update_interval):
                        result = await self.run_update_cycle()
                        if result.get("status") == "success":
                            await asyncio.sleep(self.update_interval.total_seconds())
                        else:
                            # Retry sooner on failure
                            retry_delay = timedelta(minutes=15)
                            logger.info(f"Intel feeds update failed, retrying in {retry_delay}")
                            await asyncio.sleep(retry_delay.total_seconds())
                    else:
                        remaining = self.update_interval - (datetime.utcnow() - self.last_update)
                        wait_time = min(remaining.total_seconds(), 1800)  # cap wait at 30m
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


intel_feeds_worker = IntelFeedsUpdateWorker()


async def start_intel_feeds_worker() -> None:
    await intel_feeds_worker.run_loop()
