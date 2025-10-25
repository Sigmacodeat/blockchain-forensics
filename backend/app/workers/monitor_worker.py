"""Monitor Worker
Separate process to consume events and evaluate KYT rules continuously.
Run with: `python -m app.workers.monitor_worker`
"""
from __future__ import annotations
import asyncio
import logging
import signal
from typing import Optional, Dict, Any
from collections import deque
from datetime import datetime

from app.streaming.monitor_consumer import run_once
from app.db.postgres import postgres_client
from app.services.alert_service import alert_service
from app.observability.metrics import EVENTS_BUFFERED, EVENTS_PROCESSED_BATCH, BATCH_PROCESSING_LATENCY
from app.db.redis_client import redis_client
from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))


class GracefulExit(SystemExit):
    pass


def _install_signal_handlers(loop: asyncio.AbstractEventLoop):
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(_raise_graceful_exit()))
        except NotImplementedError:
            # Windows compatibility
            pass


async def _raise_graceful_exit():
    raise GracefulExit()


async def main() -> int:
    await postgres_client.connect()
    logger.info("Monitor worker started. Evaluating events...")

    # Event buffer für Batch-Verarbeitung
    event_buffer: deque[Dict[str, Any]] = deque(maxlen=1000)  # Max 1000 Events im Buffer
    batch_size = settings.ALERT_BATCH_SIZE
    processing_interval = settings.ALERT_PROCESSING_INTERVAL_SECONDS

    processed_new = 0
    error_count = 0
    last_flush_time = asyncio.get_event_loop().time()

    try:
        while True:
            # Events sammeln
            created = await run_once(timeout=0.5)
            if created and created > 0:
                # Einzelne Events hinzufügen (aus dem Consumer)
                # In einer echten Implementierung würde hier ein Batch kommen
                # Für jetzt simulieren wir mit einzelnen Events
                for _ in range(created):
                    # Mock event für Demo - in echt würde das aus dem Consumer kommen
                    event = {
                        "entity_id": f"entity_{processed_new % 100}",
                        "event_type": "transaction",
                        "chain": "ethereum",
                        "timestamp": asyncio.get_event_loop().time()
                    }
                    event_buffer.append(event)

            current_time = asyncio.get_event_loop().time()

            # Batch flushen wenn:
            # 1. Buffer voll oder
            # 2. Zeitlimit erreicht
            should_flush = (
                len(event_buffer) >= batch_size or
                (current_time - last_flush_time) >= processing_interval
            )

            if should_flush and event_buffer:
                # Batch verarbeiten
                events_to_process = list(event_buffer)
                event_buffer.clear()

                # Update buffer metrics
                EVENTS_BUFFERED.set(len(event_buffer))

                try:
                    start_time = asyncio.get_event_loop().time()
                    alerts = await alert_service.process_event_batch(events_to_process)
                    BATCH_PROCESSING_LATENCY.observe(asyncio.get_event_loop().time() - start_time)

                    if alerts:
                        logger.info(f"Processed batch of {len(events_to_process)} events, created {len(alerts)} alerts")
                        processed_new += len(alerts)

                    # Update batch metrics
                    EVENTS_PROCESSED_BATCH.labels(batch_size=str(len(events_to_process))).inc()

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing event batch: {e}")

                last_flush_time = current_time

            await asyncio.sleep(0.05)  # Kurze Pause um CPU zu schonen

            # Heartbeat alle ~5 Sekunden
            if int(current_time) % 5 == 0:
                try:
                    await redis_client.set_worker_heartbeat(
                        name="monitor_worker",
                        payload={
                            "status": "running",
                            "last_heartbeat": datetime.utcnow().isoformat(),
                            "processed_count": processed_new,
                            "error_count": error_count,
                        },
                        ttl=15,
                    )
                except Exception:
                    pass

    except GracefulExit:
        logger.info("Graceful shutdown requested")

        # Letzte Events flushen
        if event_buffer:
            try:
                alerts = await alert_service.process_event_batch(list(event_buffer))
                if alerts:
                    logger.info(f"Final flush: processed {len(event_buffer)} events, created {len(alerts)} alerts")
            except Exception as e:
                logger.error(f"Error in final flush: {e}")
    finally:
        await postgres_client.disconnect()
        try:
            await redis_client.set_worker_heartbeat(
                name="monitor_worker",
                payload={
                    "status": "stopped",
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_count": processed_new,
                    "error_count": error_count,
                },
                ttl=30,
            )
        except Exception:
            pass

    logger.info("Monitor worker stopped. New alerts created: %s", processed_new)
    return 0


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _install_signal_handlers(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
