"""
Alert Consumer Worker

Konsumiert Alert-Events und führt Actions aus.
- Topic: alerts.events
- Verarbeitet High-Risk Alerts
- Sendet Notifications (Email, WebSocket)
- Speichert Alert History
"""
from __future__ import annotations

import asyncio
import argparse
import logging
import sys
import json
from typing import Dict, Any
from datetime import datetime

try:
    from confluent_kafka import Consumer, KafkaError  # type: ignore
    _KAFKA_AVAILABLE = True
except Exception:
    Consumer = None  # type: ignore
    KafkaError = None  # type: ignore
    _KAFKA_AVAILABLE = False

from app.config import settings
from app.messaging.kafka_client import KafkaProducerClient
from app.messaging.kafka_client import KafkaTopics
from app.bridge.registry import bridge_registry
from app.intel.travel_rule import vasp_screening_service
from app.services.email import email_service
from app.websockets.manager import manager as connection_manager
from app.db.postgres_client import postgres_client
from app.observability.metrics import KAFKA_CONSUMER_ERRORS, KAFKA_COMMITS_TOTAL

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[ALERT_CONSUMER] %(asctime)s %(levelname)s %(message)s"
)


class AlertConsumerWorker:
    """Worker für Alert Processing"""
    
    def __init__(self, group_id: str = "alert-consumer"):
        self.group_id = group_id
        self.topic = getattr(settings, "KAFKA_TOPIC_ALERTS", "alerts.events")
        
        # Kafka Consumer Config
        self.config = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000,
            "session.timeout.ms": 30000,
        }
        
        import os
        if _KAFKA_AVAILABLE and not (os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")):
            self.consumer = Consumer(self.config)  # type: ignore
        else:
            self.consumer = None  # type: ignore
        self.running = False
        self.producer = KafkaProducerClient()
        try:
            self.max_retries = int(getattr(settings, "KAFKA_MAX_PROCESS_RETRIES", 3))
        except Exception:
            self.max_retries = 3
        try:
            self.backoff_base = float(getattr(settings, "KAFKA_RETRY_BACKOFF_BASE", 0.2))
        except Exception:
            self.backoff_base = 0.2
        try:
            self.backoff_cap = float(getattr(settings, "KAFKA_RETRY_BACKOFF_CAP", 2.0))
        except Exception:
            self.backoff_cap = 2.0
    
    async def _save_alert_to_db(self, alert: Dict[str, Any]):
        """Speichert Alert in Datenbank"""
        try:
            query = """
            INSERT INTO alerts (
                alert_id, alert_type, severity, address, chain,
                risk_score, reason, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            await postgres_client.execute(
                query,
                alert.get("alert_id"),
                alert.get("alert_type", "unknown"),
                alert.get("severity", "MEDIUM"),
                alert.get("address"),
                alert.get("chain", "ethereum"),
                alert.get("risk_score", 0),
                alert.get("reason", ""),
                json.dumps(alert.get("metadata", {})),
                datetime.utcnow()
            )
            
            logger.info(f"Saved alert {alert.get('alert_id')} to database")
            
        except Exception as e:
            logger.error(f"Error saving alert to DB: {e}")
    
    async def _send_email_notification(self, alert: Dict[str, Any]):
        """Sendet Email-Notification für High-Severity Alerts"""
        try:
            severity = alert.get("severity", "MEDIUM")
            
            if severity not in ["HIGH", "CRITICAL"]:
                return
            
            # Get notification recipients (from config or DB)
            recipients = getattr(settings, "ALERT_EMAIL_RECIPIENTS", "").split(",")
            
            if not recipients or not recipients[0]:
                logger.warning("No alert email recipients configured")
                return
            
            subject = f"[{severity}] Blockchain Forensics Alert: {alert.get('alert_type')}"
            
            body = f"""
            Alert Details:
            
            Type: {alert.get('alert_type')}
            Severity: {severity}
            Address: {alert.get('address')}
            Chain: {alert.get('chain')}
            Risk Score: {alert.get('risk_score')}
            
            Reason: {alert.get('reason')}
            
            Timestamp: {alert.get('created_at')}
            Alert ID: {alert.get('alert_id')}
            
            Please investigate immediately.
            
            ---
            Blockchain Forensics Platform
            """
            
            # Send to all recipients
            for recipient in recipients:
                if recipient.strip():
                    await email_service.send_email(
                        to=recipient.strip(),
                        subject=subject,
                        body=body
                    )
            
            logger.info(f"Sent email notification for alert {alert.get('alert_id')}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _broadcast_websocket(self, alert: Dict[str, Any]):
        """Broadcastet Alert via WebSocket"""
        try:
            await connection_manager.broadcast({
                "type": "alert",
                "data": alert
            })
            logger.info(f"Broadcasted alert {alert.get('alert_id')} via WebSocket")
        except Exception as e:
            logger.error(f"Error broadcasting via WebSocket: {e}")
    
    async def _process_alert(self, message: dict) -> bool:
        """
        Verarbeitet Alert-Event
        
        Args:
            message: Alert Event
            
        Returns:
            True if successful
        """
        try:
            alert_type = message.get("alert_type")
            severity = message.get("severity", "MEDIUM")
            
            logger.info(f"Processing alert: {alert_type} severity={severity}")
            
            # 1. Save to database
            await self._save_alert_to_db(message)
            
            # 2. Broadcast via WebSocket
            await self._broadcast_websocket(message)
            
            # 3. Send email for high-severity
            await self._send_email_notification(message)
            
            # 4. Additional actions based on alert type
            if alert_type == "high_risk_transaction":
                # Could trigger automatic investigation
                logger.info(f"High risk transaction detected: {message.get('address')}")

            elif alert_type == "sanctioned_entity":
                # Critical - immediate escalation
                logger.warning(f"SANCTIONED ENTITY DETECTED: {message.get('address')}")

            elif alert_type == "pattern_detected":
                # Pattern detection (circles, layering, etc.)
                pattern = message.get("metadata", {}).get("pattern")
                logger.info(f"Pattern detected: {pattern} for {message.get('address')}")

            # 5. Bridge-specific enrichment and routing
            if alert_type in {"bridge_transfer_detected", "cross_chain_activity", "bridge_event"}:
                try:
                    meta = message.get("metadata", {}) or {}
                    contract_addr = (meta.get("contract_address") or message.get("address") or "").lower()
                    chain = (message.get("chain") or meta.get("chain") or "").lower()
                    if contract_addr and chain:
                        contract = bridge_registry.get_contract(contract_addr, chain)
                        if contract:
                            meta.update({
                                "bridge_name": contract.name,
                                "bridge_type": contract.bridge_type,
                                "counterpart_chains": contract.counterpart_chains,
                            })
                            message["metadata"] = meta
                            logger.info(f"Enriched bridge alert for {contract_addr} on {chain}: {contract.name}")
                    # Optionally forward to cross-chain topic (raw JSON)
                    if getattr(self.producer, "producer", None) is not None:
                        try:
                            payload = json.dumps(message).encode("utf-8")
                            key = (message.get("alert_id") or "").encode("utf-8") or None
                            # Use underlying producer for raw JSON
                            self.producer.producer.produce(  # type: ignore[union-attr]
                                topic=KafkaTopics.CROSS_CHAIN_ALERTS,
                                key=key,
                                value=payload,
                                headers=[("type", b"bridge")],
                                callback=self.producer._delivery_report,  # type: ignore[attr-defined]
                            )
                            self.producer.flush(5)
                            logger.info(f"Published bridge alert to {KafkaTopics.CROSS_CHAIN_ALERTS}")
                        except Exception as pub_e:
                            logger.warning(f"Failed to publish bridge alert: {pub_e}")
                except Exception as enr_e:
                    logger.error(f"Bridge enrichment failed: {enr_e}")

            # 6. Travel Rule compliance check for VASP-related transactions
            if alert_type in {"vasp_transaction", "travel_rule_violation", "high_value_transfer"}:
                try:
                    tx_data = message.get("metadata", {}) or {}
                    compliance_result = vasp_screening_service.check_travel_rule_compliance(tx_data)
                    if not compliance_result.get("compliant", True):
                        logger.warning(f"Travel Rule violation detected: {compliance_result['recommendation']}")
                        # Enhance metadata with compliance info
                        message["metadata"] = message.get("metadata", {}) or {}
                        message["metadata"]["travel_rule"] = compliance_result
                        # Optionally trigger escalation
                        if compliance_result.get("travel_rule_applies"):
                            logger.info("Triggering Travel Rule escalation alert")
                except Exception as tr_e:
                    logger.error(f"Travel Rule check failed: {tr_e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}", exc_info=True)
            return False
    
    def _consume_once(self) -> bool:
        """Konsumiert eine Nachricht"""
        if self.consumer is None:
            return False
        msg = self.consumer.poll(1.0)  # type: ignore[union-attr]
        
        if msg is None:
            return False
        
        if msg.error():
            if KafkaError is not None and msg.error().code() == KafkaError._PARTITION_EOF:  # type: ignore[union-attr]
                return False
            logger.error(f"Consumer error: {msg.error()}")
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except:
                pass
            return False
        
        try:
            value = msg.value().decode('utf-8')
            message = json.loads(value)

            if "alert_id" not in message:
                import uuid
                message["alert_id"] = str(uuid.uuid4())
            if "created_at" not in message:
                message["created_at"] = datetime.utcnow().isoformat()

            loop = asyncio.get_event_loop()
            attempt = 0
            success = False
            while attempt <= self.max_retries:
                attempt += 1
                try:
                    success = loop.run_until_complete(self._process_alert(message))
                    if success:
                        break
                except Exception as pe:
                    logger.error(f"_process_alert exception (attempt {attempt}/{self.max_retries}): {pe}")
                    success = False
                if not success and attempt <= self.max_retries:
                    import time as _t
                    delay = min(self.backoff_cap, self.backoff_base * (2 ** (attempt - 1)))
                    _t.sleep(delay)

            if not success:
                try:
                    self._send_to_dlq(msg, reason=f"processing_failed_after_{self.max_retries}_retries")
                except Exception as dlq_e:
                    logger.error(f"DLQ routing failed: {dlq_e}")

            self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
            try:
                KAFKA_COMMITS_TOTAL.labels(topic=self.topic).inc()
            except:
                pass
            return success
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            try:
                self._send_to_dlq(msg, reason="json_decode_error")
            except Exception:
                pass
            self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
            return False
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except:
                pass
            try:
                self._send_to_dlq(msg, reason=str(e))
            except Exception:
                pass
            self.consumer.commit(message=msg, asynchronous=False)
            return False

    def _send_to_dlq(self, msg, reason: str) -> None:
        try:
            if getattr(self.producer, "producer", None) is None:
                return
            topic = getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")
            self.producer.producer.produce(  # type: ignore[union-attr]
                topic=topic,
                key=msg.key(),
                value=msg.value(),
                headers=[("reason", reason.encode("utf-8", "ignore"))],
                callback=self.producer._delivery_report,  # type: ignore[attr-defined]
            )
            self.producer.flush(5)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def run(self):
        """Startet Consumer Loop"""
        if self.consumer is None:
            logger.info("Alert consumer disabled (TEST_MODE or Kafka not available)")
            return
        self.consumer.subscribe([self.topic])  # type: ignore[union-attr]
        self.running = True
        logger.info(f"Alert consumer started: topic={self.topic} group={self.group_id}")
        
        try:
            while self.running:
                self._consume_once()
        except KeyboardInterrupt:
            logger.info("Stopping alert consumer...")
        finally:
            if self.consumer is not None:
                self.consumer.close()  # type: ignore[union-attr]
    
    def stop(self):
        """Stoppt Consumer"""
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Alert Consumer Worker")
    parser.add_argument("--group", default="alert-consumer", help="Consumer group ID")
    args = parser.parse_args()
    
    worker = AlertConsumerWorker(group_id=args.group)
    worker.run()


if __name__ == "__main__":
    sys.exit(main())
