"""
Enrichment Consumer Worker

Konsumiert Enrichment-Requests und fügt Labels, Risk Scores hinzu.
- Topic: enrich.requests
- Verarbeitet Adressen/Transaktionen
- Published Results zu enrich.results
"""
from __future__ import annotations

import asyncio
import argparse
import logging
import sys
import json
from typing import Optional, Dict, Any
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
from app.enrichment.labels_service import labels_service
from app.ml.risk_scorer import risk_scorer
from app.services.compliance_service import service as compliance_service
from app.observability.metrics import KAFKA_CONSUMER_ERRORS, KAFKA_COMMITS_TOTAL

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[ENRICH_CONSUMER] %(asctime)s %(levelname)s %(message)s"
)


class EnrichmentConsumerWorker:
    """Worker für Enrichment Processing"""
    
    def __init__(self, group_id: str = "enrichment-consumer"):
        self.group_id = group_id
        self.topic = getattr(settings, "KAFKA_TOPIC_ENRICH_REQUESTS", "enrich.requests")
        self.results_topic = getattr(settings, "KAFKA_TOPIC_ENRICH_RESULTS", "enrich.results")
        
        # Kafka Consumer Config
        self.config = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 300000,  # 5 min
            "session.timeout.ms": 30000,
        }
        
        import os
        if _KAFKA_AVAILABLE and not (os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST")):
            self.consumer = Consumer(self.config)  # type: ignore
        else:
            self.consumer = None  # type: ignore
        self.producer = KafkaProducerClient()
        self.running = False
        # Retry/Backoff Settings
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
    
    async def _enrich_address(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Enriches address with labels, risk score, compliance data
        
        Args:
            address: Blockchain address
            chain: Chain name
            
        Returns:
            Enrichment data
        """
        try:
            enrichment = {
                "address": address,
                "chain": chain,
                "enriched_at": datetime.utcnow().isoformat(),
                "labels": [],
                "risk_score": 0,
                "risk_level": "LOW",
                "compliance": {}
            }
            
            # 1. Get Labels
            try:
                labels = await labels_service.get_labels(address)
                enrichment["labels"] = labels
            except Exception as e:
                logger.warning(f"Labels service error for {address}: {e}")
            
            # 2. Calculate Risk Score
            try:
                # Mock transaction data for risk scoring
                mock_tx_data = {
                    "address": address,
                    "labels": enrichment["labels"],
                    "transaction_count": 0,  # Would be fetched from DB
                    "total_volume": 0.0
                }
                risk_result = await risk_scorer.score_address(mock_tx_data)
                enrichment["risk_score"] = risk_result.get("risk_score", 0)
                enrichment["risk_level"] = risk_result.get("risk_level", "LOW")
                enrichment["risk_factors"] = risk_result.get("factors", [])
            except Exception as e:
                logger.warning(f"Risk scoring error for {address}: {e}")
            
            # 3. Compliance Screening
            try:
                screening = compliance_service.screen(chain, address)
                enrichment["compliance"] = {
                    "risk_score": screening.risk_score,
                    "categories": screening.categories,
                    "reasons": screening.reasons,
                    "watchlisted": screening.watchlisted
                }
            except Exception as e:
                logger.warning(f"Compliance screening error for {address}: {e}")
            
            return enrichment
            
        except Exception as e:
            logger.error(f"Error enriching address {address}: {e}")
            return {"address": address, "error": str(e)}
    
    async def _process_enrichment_request(self, message: dict) -> Optional[dict]:
        """
        Verarbeitet Enrichment-Request
        
        Args:
            message: Enrichment Request
            
        Returns:
            Enrichment Result
        """
        try:
            request_type = message.get("type", "address")
            request_id = message.get("request_id")
            
            logger.info(f"Processing enrichment request: {request_id} type={request_type}")
            
            if request_type == "address":
                address = message.get("address")
                chain = message.get("chain", "ethereum")
                
                enrichment = await self._enrich_address(address, chain)
                enrichment["request_id"] = request_id
                enrichment["request_type"] = request_type
                
                return enrichment
            
            elif request_type == "batch":
                # Batch processing
                addresses = message.get("addresses", [])
                chain = message.get("chain", "ethereum")
                
                results = []
                for addr in addresses[:100]:  # Limit to 100 per request
                    enrichment = await self._enrich_address(addr, chain)
                    results.append(enrichment)
                
                return {
                    "request_id": request_id,
                    "request_type": "batch",
                    "results": results,
                    "enriched_at": datetime.utcnow().isoformat()
                }
            
            else:
                logger.warning(f"Unknown request type: {request_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing enrichment request: {e}", exc_info=True)
            return None
    
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
            # Parse message
            value = msg.value().decode('utf-8')
            message = json.loads(value)

            # Process enrichment request with retry/backoff
            loop = asyncio.get_event_loop()
            attempt = 0
            result = None
            while attempt <= self.max_retries:
                attempt += 1
                try:
                    result = loop.run_until_complete(self._process_enrichment_request(message))
                    if result:
                        break
                except Exception as pe:
                    logger.error(f"_process_enrichment_request exception (attempt {attempt}/{self.max_retries}): {pe}")
                    result = None
                if not result and attempt <= self.max_retries:
                    import time as _t
                    delay = min(self.backoff_cap, self.backoff_base * (2 ** (attempt - 1)))
                    _t.sleep(delay)

            if result:
                # Publish result
                try:
                    self.producer.send_event(
                        event=result,
                        topic=self.results_topic,
                        key=result.get("request_id")
                    )
                except Exception as pub_e:
                    logger.warning(f"Publish enrichment result failed: {pub_e}")
                # Commit offset
                self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
                try:
                    KAFKA_COMMITS_TOTAL.labels(topic=self.topic).inc()
                except:
                    pass
                return True
            else:
                # Final failure: route to DLQ and commit
                try:
                    self._send_to_dlq(msg, reason=f"processing_failed_after_{self.max_retries}_retries")
                except Exception as dlq_e:
                    logger.error(f"DLQ routing failed: {dlq_e}")
                try:
                    self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
                    KAFKA_COMMITS_TOTAL.labels(topic=self.topic).inc()
                except Exception:
                    pass
                return False
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            self.consumer.commit(message=msg, asynchronous=False)  # type: ignore[union-attr]
            return False
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except:
                pass
            self.consumer.commit(message=msg, asynchronous=False)
            return False
    
    def run(self):
        """Startet Consumer Loop"""
        if self.consumer is None:
            logger.info("Enrichment consumer disabled (TEST_MODE or Kafka not available)")
            return
        self.consumer.subscribe([self.topic])  # type: ignore[union-attr]
        self.running = True
        logger.info(f"Enrichment consumer started: topic={self.topic} group={self.group_id}")
        
        try:
            while self.running:
                self._consume_once()
        except KeyboardInterrupt:
            logger.info("Stopping enrichment consumer...")
        finally:
            if self.consumer is not None:
                self.consumer.close()  # type: ignore[union-attr]
            self.producer.flush()
    
    def stop(self):
        """Stoppt Consumer"""
        self.running = False

    def _send_to_dlq(self, msg, reason: str) -> None:
        """Sendet die Original-Nachricht in das DLQ-Topic mit Reason-Header."""
        try:
            if getattr(self.producer, "producer", None) is None:
                return
            topic = getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")
            self.producer.producer.produce(  # type: ignore[union-attr]
                topic=topic,
                key=msg.key(),
                value=msg.value(),
                headers=[("reason", reason.encode("utf-8", "ignore"))],
                callback=getattr(self.producer, "_delivery_report", None),  # type: ignore[attr-defined]
            )
            # Flush via producer client if verfügbar
            try:
                self.producer.flush(5)  # type: ignore[union-attr]
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enrichment Consumer Worker")
    parser.add_argument("--group", default="enrichment-consumer", help="Consumer group ID")
    args = parser.parse_args()
    
    worker = EnrichmentConsumerWorker(group_id=args.group)
    worker.run()


if __name__ == "__main__":
    sys.exit(main())
