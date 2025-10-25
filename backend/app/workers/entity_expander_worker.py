"""
Entity Database Expansion Background Worker
===========================================

Automatically expands and updates entity database every 24 hours
Target: 5,000+ → 12,000+ labels (Chainalysis parity)

Schedule:
- Initial run on startup
- Daily updates at 02:00 UTC
- Manual trigger via API: POST /api/v1/admin/entity-expansion/trigger
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta

from app.ingest.entity_database_expander import run_expansion

logger = logging.getLogger(__name__)


class EntityExpanderWorker:
    """Background worker for entity database expansion"""
    
    def __init__(self):
        self.running = False
        self.last_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background worker"""
        if self.running:
            logger.warning("Entity expander worker already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._worker_loop())
        logger.info("Entity expander worker started")
    
    async def stop(self):
        """Stop the background worker"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Entity expander worker stopped")
    
    async def _worker_loop(self):
        """Main worker loop"""
        # Initial run on startup
        await self._run_expansion()
        
        # Periodic updates
        while self.running:
            try:
                # Wait until next scheduled run (24 hours)
                await asyncio.sleep(86400)  # 24 hours
                await self._run_expansion()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}", exc_info=True)
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _run_expansion(self):
        """Run entity database expansion"""
        try:
            logger.info("Starting scheduled entity database expansion...")
            stats = await run_expansion()
            self.last_run = datetime.utcnow()
            
            logger.info(
                f"Entity expansion complete: {stats['total_labels']} labels, "
                f"{stats['inserted']} new, {stats['existing']} updated"
            )
        except Exception as e:
            logger.error(f"Entity expansion failed: {e}", exc_info=True)
    
    async def trigger_manual_run(self) -> Dict[str, Any]:
        """Manually trigger an expansion run"""
        logger.info("Manual entity expansion triggered")
        return await run_expansion()


# Singleton instance
entity_expander_worker = EntityExpanderWorker()
