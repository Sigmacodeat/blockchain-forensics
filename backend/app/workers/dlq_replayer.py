"""
DLQ Replayer Worker

- Scannt DLQ-Topic nach Nachrichten mit Filtern (Topic, Key, Zeitbereich)
- Replayt gefilterte Nachrichten auf ursprüngliches Topic
- Throttle: Rate-Limiting für Replay
- Metriken: Replay-Counter, Fehler

Startbeispiel:
python -m app.workers.dlq_replayer --filter-topic ingest.events --since 2023-01-01 --until 2023-12-31 --throttle 10 --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from confluent_kafka import Consumer, Producer, KafkaError, KafkaException

from app.config import settings
from app.observability.metrics import DLQ_REPLAY_TOTAL, DLQ_REPLAY_ERRORS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[DLQ-REPLAYER] %(asctime)s %(levelname)s %(message)s")


class DLQReplayer:
    def __init__(self, throttle: int = 10):
        self.throttle = throttle
        self.dlq_topic = getattr(settings, "KAFKA_DLQ_TOPIC", "dlq.events")
        self.producer = Producer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        })
    
    def _matches_filter(self, msg, filter_topic: Optional[str], filter_key: Optional[str], since: Optional[datetime], until: Optional[datetime]) -> bool:
        # Topic filter
        if filter_topic:
            try:
                headers = msg.headers() or []
                original_topic = None
                for k, v in headers:
                    if k == "original_topic":
                        original_topic = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                        break
                if original_topic != filter_topic:
                    return False
            except Exception:
                return False
        
        # Key filter
        if filter_key:
            try:
                msg_key = msg.key().decode("utf-8") if msg.key() else None
                if msg_key != filter_key:
                    return False
            except Exception:
                return False
        
        # Time filter
        if since or until:
            try:
                timestamp = msg.timestamp()[1] / 1000  # milliseconds to seconds
                msg_time = datetime.fromtimestamp(timestamp)
                if since and msg_time < since:
                    return False
                if until and msg_time > until:
                    return False
            except Exception:
                return False
        
        return True
    
    async def replay_filtered(
        self,
        filter_topic: Optional[str] = None,
        filter_key: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        dry_run: bool = False,
        max_messages: int = 1000
    ) -> Dict[str, Any]:
        """Scan DLQ and replay filtered messages"""
        
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": f"dlq-replayer-{datetime.now().isoformat()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "enable.partition.eof": True,
            "session.timeout.ms": 10000,
        }
        
        consumer = Consumer(conf)
        consumer.subscribe([self.dlq_topic])
        logger.info(f"Scanning DLQ topic: {self.dlq_topic}")
        
        replayed = 0
        errors = 0
        scanned = 0
        
        try:
            while scanned < max_messages:
                msg = consumer.poll(1.0)
                if msg is None:
                    break
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Poll error: {msg.error()}")
                    errors += 1
                    continue
                
                scanned += 1
                
                if not self._matches_filter(msg, filter_topic, filter_key, since, until):
                    continue
                
                # Extract original topic from headers
                original_topic = None
                try:
                    headers = msg.headers() or []
                    for k, v in headers:
                        if k == "original_topic":
                            original_topic = v.decode("utf-8") if isinstance(v, bytes) else str(v)
                            break
                except Exception:
                    pass
                
                if not original_topic:
                    logger.warning(f"No original_topic header found, skipping message at offset {msg.offset()}")
                    continue
                
                if dry_run:
                    logger.info(f"DRY-RUN: Would replay message to {original_topic} (offset {msg.offset()})")
                else:
                    try:
                        # Replay to original topic
                        self.producer.produce(
                            topic=original_topic,
                            key=msg.key(),
                            value=msg.value(),
                            headers=msg.headers(),
                        )
                        self.producer.flush(5)
                        replayed += 1
                        logger.info(f"Replayed message to {original_topic} (offset {msg.offset()})")
                        
                        # Throttle
                        await asyncio.sleep(1.0 / self.throttle)
                        
                        DLQ_REPLAY_TOTAL.inc()
                    except Exception as e:
                        logger.error(f"Replay failed: {e}")
                        errors += 1
                        DLQ_REPLAY_ERRORS.inc()
        
        finally:
            consumer.close()
            self.producer.flush()
        
        return {
            "scanned": scanned,
            "replayed": replayed,
            "errors": errors,
            "dry_run": dry_run
        }


def main():
    parser = argparse.ArgumentParser(description="DLQ Replayer Worker")
    parser.add_argument("--filter-topic", help="Filter by original topic")
    parser.add_argument("--filter-key", help="Filter by message key")
    parser.add_argument("--since", help="Filter since date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Filter until date (YYYY-MM-DD)")
    parser.add_argument("--throttle", type=int, default=10, help="Replay rate per second")
    parser.add_argument("--max-messages", type=int, default=1000, help="Max messages to scan")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    args = parser.parse_args()
    
    since = datetime.fromisoformat(args.since) if args.since else None
    until = datetime.fromisoformat(args.until) if args.until else None
    
    replayer = DLQReplayer(throttle=args.throttle)
    
    async def run():
        result = await replayer.replay_filtered(
            filter_topic=args.filter_topic,
            filter_key=args.filter_key,
            since=since,
            until=until,
            dry_run=args.dry_run,
            max_messages=args.max_messages
        )
        print(json.dumps(result, indent=2))
    
    asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())
