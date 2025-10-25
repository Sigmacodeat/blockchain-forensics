"""
Alert Batching Service
Optimizes alert processing by batching similar alerts together
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict

from app.services.alert_engine import Alert, AlertSeverity, AlertType
from app.observability.metrics import (
    ALERT_BATCH_SIZE, ALERT_BATCH_PROCESSING_TIME,
    ALERT_BATCHES_CREATED, ALERT_BATCHES_PROCESSED
)

logger = logging.getLogger(__name__)


@dataclass
class AlertBatch:
    """Represents a batch of similar alerts"""
    batch_id: str
    alert_type: AlertType
    severity: AlertSeverity
    entity_type: str  # 'address', 'transaction', etc.
    entity_ids: List[str] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None

    def add_alert(self, alert: Alert) -> None:
        """Add an alert to this batch"""
        if alert.alert_id not in [a.alert_id for a in self.alerts]:
            self.alerts.append(alert)
            if hasattr(alert, 'address') and alert.address:
                if alert.address not in self.entity_ids:
                    self.entity_ids.append(alert.address)

    def size(self) -> int:
        """Get batch size"""
        return len(self.alerts)

    def is_expired(self, max_age_seconds: int = 300) -> bool:
        """Check if batch has expired"""
        return (datetime.utcnow() - self.created_at).total_seconds() > max_age_seconds

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary"""
        return {
            "batch_id": self.batch_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "entity_count": len(self.entity_ids),
            "alert_count": self.size(),
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_duration": self.processing_duration
        }


class AlertBatchingService:
    """
    Service for batching similar alerts to improve processing efficiency

    Features:
    - Groups alerts by type, severity, and entity
    - Configurable batch sizes and timeouts
    - Automatic batch processing
    - Batch deduplication
    """

    def __init__(self):
        self.batches: Dict[str, AlertBatch] = {}
        self.batch_configs = {
            AlertType.HIGH_RISK_ADDRESS: {"max_size": 50, "max_age": 60},
            AlertType.SANCTIONED_ENTITY: {"max_size": 25, "max_age": 30},
            AlertType.LARGE_TRANSFER: {"max_size": 100, "max_age": 120},
            AlertType.MIXER_USAGE: {"max_size": 30, "max_age": 45},
            AlertType.SUSPICIOUS_PATTERN: {"max_size": 75, "max_age": 90},
            AlertType.BRIDGE_ACTIVITY: {"max_size": 40, "max_age": 60},
            AlertType.NEW_HIGH_RISK_CONNECTION: {"max_size": 20, "max_age": 30}
        }

        # Start background processor
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self) -> None:
        """Start the background batch processor"""
        if not self._running:
            self._running = True
            self._processor_task = asyncio.create_task(self._process_batches_loop())

    def stop(self) -> None:
        """Stop the background batch processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()

    def add_alert(self, alert: Alert) -> Optional[AlertBatch]:
        """
        Add an alert to appropriate batch

        Returns the batch if it was processed immediately, None otherwise
        """
        batch_key = self._get_batch_key(alert)

        if batch_key not in self.batches:
            # Create new batch
            batch = AlertBatch(
                batch_id=f"batch_{alert.alert_type.value}_{datetime.utcnow().timestamp()}",
                alert_type=alert.alert_type,
                severity=alert.severity,
                entity_type=self._get_entity_type(alert)
            )
            self.batches[batch_key] = batch
            ALERT_BATCHES_CREATED.inc()

        batch = self.batches[batch_key]
        batch.add_alert(alert)

        # Check if batch should be processed now
        config = self.batch_configs.get(alert.alert_type, {"max_size": 50, "max_age": 60})
        should_process = (
            batch.size() >= config["max_size"] or
            batch.is_expired(config["max_age"])
        )

        if should_process:
            return self._process_batch(batch_key)

        return None

    def force_process_all(self) -> List[AlertBatch]:
        """Force process all pending batches"""
        processed = []
        for batch_key in list(self.batches.keys()):
            batch = self._process_batch(batch_key)
            if batch:
                processed.append(batch)
        return processed

    def get_batch_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        total_batches = len(self.batches)
        total_alerts = sum(batch.size() for batch in self.batches.values())

        by_type = defaultdict(int)
        for batch in self.batches.values():
            by_type[batch.alert_type.value] += 1

        return {
            "total_batches": total_batches,
            "total_pending_alerts": total_alerts,
            "batches_by_type": dict(by_type),
            "oldest_batch_age": max(
                (datetime.utcnow() - batch.created_at).total_seconds()
                for batch in self.batches.values()
            ) if self.batches else 0
        }

    def _get_batch_key(self, alert: Alert) -> str:
        """Generate batch key for grouping similar alerts"""
        entity_type = self._get_entity_type(alert)
        return f"{alert.alert_type.value}_{alert.severity.value}_{entity_type}"

    def _get_entity_type(self, alert: Alert) -> str:
        """Determine entity type for batching"""
        if hasattr(alert, 'address') and alert.address:
            return "address"
        elif hasattr(alert, 'tx_hash') and alert.tx_hash:
            return "transaction"
        else:
            return "generic"

    def _process_batch(self, batch_key: str) -> Optional[AlertBatch]:
        """Process a specific batch"""
        if batch_key not in self.batches:
            return None

        batch = self.batches[batch_key]

        # Update metrics
        ALERT_BATCH_SIZE.observe(batch.size())

        # Process batch (in real implementation, this would trigger notifications, etc.)
        start_time = datetime.utcnow()
        try:
            # Simulate processing time based on batch size
            processing_time = min(batch.size() * 0.01, 5.0)  # Max 5 seconds
            time.sleep(processing_time)

            batch.processed_at = datetime.utcnow()
            batch.processing_duration = (batch.processed_at - start_time).total_seconds()

            # Update metrics
            ALERT_BATCH_PROCESSING_TIME.observe(batch.processing_duration)
            ALERT_BATCHES_PROCESSED.inc()

            logger.info(f"Processed alert batch {batch.batch_id} with {batch.size()} alerts")

        except Exception as e:
            logger.error(f"Error processing batch {batch.batch_id}: {e}")
            batch.processing_duration = (datetime.utcnow() - start_time).total_seconds()
        finally:
            # Remove processed batch
            del self.batches[batch_key]

        return batch

    async def _process_batches_loop(self) -> None:
        """Background loop to process expired batches"""
        while self._running:
            try:
                # Check for expired batches every 30 seconds
                await asyncio.sleep(30)

                expired_keys = []
                for batch_key, batch in self.batches.items():
                    config = self.batch_configs.get(batch.alerts[0].alert_type if batch.alerts else AlertType.HIGH_RISK_ADDRESS,
                                                   {"max_size": 50, "max_age": 60})
                    if batch.is_expired(config["max_age"]):
                        expired_keys.append(batch_key)

                # Process expired batches
                for batch_key in expired_keys:
                    self._process_batch(batch_key)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying


# Global batching service instance
alert_batching_service = AlertBatchingService()


def start_alert_batching() -> None:
    """Start the alert batching service"""
    alert_batching_service.start()


def stop_alert_batching() -> None:
    """Stop the alert batching service"""
    alert_batching_service.stop()


def get_batching_stats() -> Dict[str, Any]:
    """Get current batching statistics"""
    return alert_batching_service.get_batch_stats()
