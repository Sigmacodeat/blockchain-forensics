"""
Sanctions Update Worker
=======================

Background worker that periodically fetches and updates sanctions data
from multiple sources (OFAC, EU, UK, UN).

Features:
- Configurable refresh intervals per source
- Incremental updates with ETags/Last-Modified
- Error handling and metrics
- DB integration for persistent storage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

from app.intel.sanctions import sanctions_indexer
from app.audit.logger import log_data_access

logger = logging.getLogger(__name__)


class SanctionsUpdateWorker:
    """
    Background worker for sanctions data updates
    """

    def __init__(self):
        self.running = False
        self.worker_name = "sanctions_update"
        self.update_interval = self._get_update_interval()
        self.last_update: Optional[datetime] = None

    def _get_update_interval(self) -> timedelta:
        """Get update interval from environment or default"""
        try:
            hours = int(os.getenv("SANCTIONS_UPDATE_INTERVAL_HOURS", "6"))
            return timedelta(hours=hours)
        except Exception:
            return timedelta(hours=6)  # Default: every 6 hours

    async def _heartbeat(self):
        """Update worker heartbeat metric"""
        try:
            WORKER_LAST_HEARTBEAT.labels(worker=self.worker_name).set(datetime.utcnow().timestamp())
        except Exception:
            pass

    async def _set_status(self, status: int):
        """Set worker status metric"""
        try:
            WORKER_STATUS.labels(worker=self.worker_name).set(status)
        except Exception as e:
            logger.error(f"Failed to set worker status: {e}")

    async def run_update_cycle(self) -> Dict[str, Any]:
        """
        Run a single sanctions update cycle
        Returns update statistics
        """
        try:
            await self._heartbeat()

            logger.info("Starting sanctions update cycle")
            result = await sanctions_indexer.run_update()

            # Update metrics
            try:
                WORKER_PROCESSED_TOTAL.labels(worker=self.worker_name).inc()
            except Exception as e:
                logger.error(f"Failed to increment processed counter: {e}")

            self.last_update = datetime.utcnow()

            if result.get("status") == "success":
                # Audit log successful update
                try:
                    await log_data_access(
                        user_id="system",
                        resource_type="sanctions_data",
                        resource_id="bulk_update",
                        action="update",
                        details=result
                    )
                except Exception as e:
                    logger.error(f"Failed to audit log sanctions update: {e}")

                logger.info(f"Sanctions update completed: {result}")
            else:
                logger.error(f"Sanctions update failed: {result}")
                try:
                    WORKER_ERRORS_TOTAL.labels(worker=self.worker_name).inc()
                except Exception as e:
                    logger.error(f"Failed to increment error counter: {e}")

            return result

        except Exception as e:
            logger.error(f"Sanctions update cycle failed: {e}")
            try:
                WORKER_ERRORS_TOTAL.labels(worker=self.worker_name).inc()
            except Exception as e:
                logger.error(f"Failed to increment error counter in exception: {e}")
            return {"status": "error", "error": str(e)}

    async def run_loop(self):
        """Main worker loop"""
        self.running = True
        await self._set_status(1)

        logger.info(f"Starting {self.worker_name} worker with interval: {self.update_interval}")

        try:
            while self.running:
                try:
                    # Check if it's time for an update
                    if (self.last_update is None or
                        datetime.utcnow() - self.last_update > self.update_interval):

                        result = await self.run_update_cycle()

                        # If update was successful, wait for next interval
                        if result.get("status") == "success":
                            await asyncio.sleep(self.update_interval.total_seconds())
                        else:
                            # If update failed, wait shorter time before retry
                            retry_delay = timedelta(minutes=30)
                            logger.info(f"Update failed, retrying in {retry_delay}")
                            await asyncio.sleep(retry_delay.total_seconds())
                    else:
                        # Wait until next update time
                        remaining = self.update_interval - (datetime.utcnow() - self.last_update)
                        wait_time = min(remaining.total_seconds(), 3600)  # Max 1 hour
                        await asyncio.sleep(wait_time)

                except asyncio.CancelledError:
                    logger.info(f"{self.worker_name} worker cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in {self.worker_name} worker loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retry

        finally:
            await self._set_status(0)
            logger.info(f"{self.worker_name} worker stopped")

    def stop(self):
        """Stop the worker"""
        logger.info(f"Stopping {self.worker_name} worker")
        self.running = False


# Global worker instance
sanctions_worker = SanctionsUpdateWorker()


async def start_sanctions_worker():
    """Start the sanctions worker as background task"""
    await sanctions_worker.run_loop()


# Convenience function for testing
async def run_sanctions_update_once() -> Dict[str, Any]:
    """Run a single sanctions update (for testing)"""
    return await sanctions_worker.run_update_cycle()
