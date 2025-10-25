from __future__ import annotations
import asyncio
import logging
import os

from app.workers.dsr_worker import DSRWorker

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("dsr_cli")

async def main():
    w = DSRWorker(interval_seconds=300)
    stats = await w.run_once()
    logger.info(f"DSR one-shot processed: exports={stats['exports']}, deletes={stats['deletes']}")

if __name__ == "__main__":
    asyncio.run(main())
