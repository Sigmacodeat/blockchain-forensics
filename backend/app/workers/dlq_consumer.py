"""
DLQ Consumer Worker

- Konsumiert Nachrichten vom DLQ-Topic (konfigurierbar via KAFKA_DLQ_TOPIC)
- Loggt Reason-Header und grundlegende Metadaten
- Optionales Requeue auf ein Ziel-Topic via --requeue-to <topic>
- Erhöht Prometheus-Metriken (KAFKA_DLQ_MESSAGES wird beim Routing erhöht; hier zählen wir Commits/Fehler)

Startbeispiel:
python -m app.workers.dlq_consumer --group dlq-monitor --timeout 2 --requeue-to enrich.results
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

from app.config import settings
from app.messaging.kafka_client import KafkaProducerClient
from app.observability.metrics import KAFKA_CONSUMER_ERRORS, KAFKA_COMMITS_TOTAL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[DLQ] %(asctime)s %(levelname)s %(message)s")


def _get_reason(msg) -> Optional[str]:
    try:
        headers = msg.headers() or []
        for k, v in headers:
            if k == "reason":
                return v.decode("utf-8", "ignore") if isinstance(v, (bytes, bytearray)) else str(v)
    except Exception:
        return None
    return None


def _consume_once(consumer: Consumer, requeue_to: Optional[str]) -> bool:
    msg = consumer.poll(1.0)
    if msg is None:
        return False
    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            return False
        logger.error(f"Poll error: {msg.error()}")
        try:
            KAFKA_CONSUMER_ERRORS.inc()
        except Exception:
            pass
        return False

    key = None
    try:
        key = msg.key().decode("utf-8") if msg.key() else None
    except Exception:
        key = None

    reason = _get_reason(msg) or "unknown"
    logger.info(f"DLQ message received: partition={msg.partition()} offset={msg.offset()} key={key} reason={reason} size={len(msg.value() or b'')}B")

    # Optional: requeue to another topic (raw bytes)
    if requeue_to:
        try:
            prod = KafkaProducerClient()
            prod.producer.produce(
                topic=requeue_to,
                key=msg.key(),
                value=msg.value(),
                headers=msg.headers() or [],
                callback=prod._delivery_report,
            )
            prod.flush(10)
            logger.info(f"Requeued DLQ message to '{requeue_to}'")
        except Exception as e:
            logger.error(f"Requeue failed: {e}")
            try:
                KAFKA_CONSUMER_ERRORS.inc()
            except Exception:
                pass

    # Commit DLQ message
    try:
        consumer.commit(message=msg, asynchronous=False)
        try:
            KAFKA_COMMITS_TOTAL.labels(topic=getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")).inc()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Commit failed: {e}")
        try:
            KAFKA_CONSUMER_ERRORS.inc()
        except Exception:
            pass
    return True


def main():
    parser = argparse.ArgumentParser(description="DLQ Consumer Worker")
    parser.add_argument("--group", default="dlq-consumer", help="Kafka consumer group id")
    parser.add_argument("--timeout", type=float, default=1.0, help="Poll timeout in seconds")
    parser.add_argument("--requeue-to", default=None, help="Optional target topic to requeue messages")
    args = parser.parse_args()

    conf = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "group.id": args.group,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "enable.partition.eof": True,
        "session.timeout.ms": 10000,
        "max.poll.interval.ms": 300000,
    }
    consumer = Consumer(conf)
    topic = getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")
    consumer.subscribe([topic])
    logger.info(f"DLQ consumer started: topic={topic} group={args.group}")

    try:
        while True:
            _consume_once(consumer, args.requeue_to)
    except KeyboardInterrupt:
        logger.info("Stopping DLQ consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    sys.exit(main())
