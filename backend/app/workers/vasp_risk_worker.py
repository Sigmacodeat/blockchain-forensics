"""
VASP Risk Update Worker
- Periodically scores VASPs using the VaspRiskRegistry and stores last records in memory
- ENV-gated; safe to run in production with proper persistence later

ENVs:
- ENABLE_VASP_RISK_WORKER=1 to enable
- VASP_RISK_UPDATE_INTERVAL_MINUTES (default: 1440 = daily)
"""
from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from app.compliance.vasp.service import vasp_service
from app.compliance.vasp_risk import vasp_risk_registry

logger = logging.getLogger(__name__)


class VaspRiskWorker:
    def __init__(self) -> None:
        self.running: bool = False
        self.worker_name: str = "vasp_risk_update"
        self.update_interval: timedelta = self._get_update_interval()
        self._task: Optional[asyncio.Task] = None

    def _get_update_interval(self) -> timedelta:
        try:
            minutes = int(os.getenv("VASP_RISK_UPDATE_INTERVAL_MINUTES", "1440"))
            return timedelta(minutes=minutes)
        except Exception:
            return timedelta(minutes=1440)

    async def run_once(self) -> Dict[str, Any]:
        try:
            logger.info("Starting VASP risk update cycle")
            # fetch all vasps via broad search (empty query returns all, capped by limit)
            vasps = vasp_service.search(query="", limit=10000)
            vasp_ids: List[str] = [v.id for v in vasps]
            recs = await vasp_risk_registry.score_many(vasp_ids)
            logger.info(f"Completed VASP risk update cycle: {len(recs)} scored")
            return {"status": "success", "scored": len(recs), "total": len(vasp_ids)}
        except Exception as e:
            logger.error(f"VASP risk update cycle failed: {e}")
            return {"status": "error", "error": str(e)}

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"{self.worker_name} started with interval {self.update_interval}")

    async def _run_loop(self) -> None:
        while self.running:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"{self.worker_name} loop error: {e}")
            # sleep until next interval
            try:
                await asyncio.sleep(self.update_interval.total_seconds())
            except asyncio.CancelledError:
                break

    def stop(self) -> None:
        self.running = False
        if self._task and not self._task.done():
            try:
                self._task.cancel()
            except Exception:
                pass
        logger.info(f"{self.worker_name} stopped")


vasp_risk_worker = VaspRiskWorker()


async def start_vasp_risk_worker() -> None:
    await vasp_risk_worker.start()


def stop_vasp_risk_worker() -> None:
    vasp_risk_worker.stop()


async def run_vasp_risk_update_once() -> Dict[str, Any]:
    return await vasp_risk_worker.run_once()
