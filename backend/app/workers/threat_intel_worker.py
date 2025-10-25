"""
Threat Intelligence Feed Updater Worker
=======================================

Background worker that periodically updates threat intelligence feeds
and integrates with the enrichment pipeline.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from app.intel.service import get_threat_intel_service
from app.messaging.kafka_client import KafkaTopics
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class ThreatIntelUpdater:
    """Worker for updating threat intelligence feeds"""

    def __init__(self):
        self.running = False
        self.update_interval = timedelta(hours=1)  # Update every hour
        self.processed_updates = 0
        self.error_count = 0

    async def start(self):
        """Start the feed updater worker"""
        self.running = True
        logger.info("Starting Threat Intelligence Feed Updater")

        while self.running:
            try:
                await self._update_feeds()
                self.processed_updates += 1
                await self._heartbeat(status="running")
                await asyncio.sleep(self.update_interval.total_seconds())
            except Exception as e:
                logger.error(f"Error in feed updater: {e}")
                self.error_count += 1
                await self._heartbeat(status="error")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def stop(self):
        """Stop the feed updater worker"""
        self.running = False
        logger.info("Stopping Threat Intelligence Feed Updater")
        # Fire and forget final heartbeat
        try:
            asyncio.create_task(self._heartbeat(status="stopped"))
        except Exception as e:
            logger.error(f"Failed to send final heartbeat: {e}")

    async def _update_feeds(self):
        """Update all feeds and publish results"""
        logger.info("Updating threat intelligence feeds...")

        try:
            service = get_threat_intel_service()
            results = await service.update_all_feeds()

            # Publish update summary to Kafka for monitoring
            await self._publish_update_summary(results)

            logger.info(f"Feed update completed: {results}")

        except Exception as e:
            logger.error(f"Error updating feeds: {e}")

    async def _publish_update_summary(self, results: dict):
        """Publish feed update summary to Kafka"""
        try:
            from app.messaging.kafka_client import KafkaProducerClient

            producer = KafkaProducerClient()
            summary_event = {
                "event_id": f"feed_update_{datetime.utcnow().isoformat()}",
                "event_type": "threat_intel_feeds_updated",
                "timestamp": datetime.utcnow().isoformat(),
                "data": results
            }

            producer.produce_event(
                topic=KafkaTopics.AUDIT_LOG,
                event=summary_event
            )

        except Exception as e:
            logger.error(f"Failed to publish feed update summary: {e}")

    async def _heartbeat(self, status: str = "running"):
        """Send heartbeat to Redis for system monitoring."""
        try:
            await redis_client.set_worker_heartbeat(
                name="threat_intel_worker",
                payload={
                    "status": status,
                    "last_heartbeat": datetime.utcnow().isoformat(),
                    "processed_count": self.processed_updates,
                    "error_count": self.error_count,
                },
                ttl=3600,  # long TTL since updates are hourly
            )
        except Exception:
            # Do not crash worker due to monitoring failures
            pass


# Global worker instance
threat_intel_updater = ThreatIntelUpdater()


async def start_threat_intel_updater():
    """Start the threat intelligence updater as background task"""
    await threat_intel_updater.start()


def stop_threat_intel_updater():
    """Stop the threat intelligence updater"""
    threat_intel_updater.stop()
