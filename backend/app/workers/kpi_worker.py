"""KPI Background Worker
Periodisch KPIs berechnen und im Redis-Cache vorwärmen.
Start: via lifespan in app.main
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Iterable, Tuple

from app.services.kpi_service import kpi_service
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class KpiWorker:
    def __init__(self, presets: Iterable[Tuple[int, int]] | None = None, interval_seconds: int = 60):
        # presets: Liste von (days, sla_hours)
        self.presets = list(presets or [(30, 48), (7, 48)])
        self.interval = max(15, int(interval_seconds))
        self._stopping = asyncio.Event()

    async def start(self):
        """Startet den Loop bis stop() aufgerufen wird."""
        logger.info("KPI worker started (interval=%ss, presets=%s)", self.interval, self.presets)
        # Redis-Verbindung optional herstellen
        try:
            await redis_client._ensure_connected()  # type: ignore[attr-defined]
        except Exception:
            pass
        while not self._stopping.is_set():
            try:
                # Presets nacheinander berechnen (wird im Service gecached)
                for days, sla in self.presets:
                    try:
                        await kpi_service.get_kpis(days=days, sla_hours=sla)
                    except Exception as e:
                        logger.warning("KPI precompute failed for (%s,%s): %s", days, sla, e)
                await asyncio.wait_for(self._stopping.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                # weiterlaufen
                continue
            except Exception as e:
                logger.error("KPI worker loop error: %s", e)
                await asyncio.sleep(0.5)
        logger.info("KPI worker stopped")

    def stop(self):
        self._stopping.set()


_kpi_worker: KpiWorker | None = None


def start_kpi_worker(presets: Iterable[Tuple[int, int]] | None = None, interval_seconds: int = 60):
    global _kpi_worker
    _kpi_worker = KpiWorker(presets=presets, interval_seconds=interval_seconds)
    return _kpi_worker


def stop_kpi_worker():
    global _kpi_worker
    if _kpi_worker is not None:
        _kpi_worker.stop()
