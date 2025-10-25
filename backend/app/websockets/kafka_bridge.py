"""
Kafka → WebSocket Bridge
=========================

Bridges Kafka events to WebSocket clients for real-time updates.
Consumes from Kafka topics and broadcasts to subscribed WebSocket clients.

Features:
- Real-Time Trace Progress
- Live Alerts
- Bridge Detection Notifications
- System Events
"""

import logging
import asyncio
import json
from typing import Dict, Optional
from confluent_kafka import Consumer, KafkaError

from app.websockets.manager import manager
from app.config import settings

logger = logging.getLogger(__name__)


class KafkaWebSocketBridge:
    """
    Bridges Kafka events to WebSocket connections
    """
    
    def __init__(self):
        self.consumer: Optional[Consumer] = None
        self.running = False
        self.enabled = getattr(settings, "ENABLE_KAFKA_STREAMING", False)
        
        # Topics to bridge
        self.bridge_topics = [
            "alerts",              # High-priority alerts
            "trace.progress",      # Trace progress updates
            "bridge.detected",     # Bridge detections
            "enrichment.completed" # Enrichment results
        ]
        
        if self.enabled:
            self._init_consumer()
    
    def _init_consumer(self):
        """Initialize Kafka consumer for bridge"""
        try:
            config = {
                'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
                'group.id': 'websocket-bridge-group',
                'auto.offset.reset': 'latest',  # Only new messages
                'enable.auto.commit': True,
                'session.timeout.ms': 60000,
            }
            
            self.consumer = Consumer(config)
            self.consumer.subscribe(self.bridge_topics)
            
            logger.info(f"Kafka-WebSocket bridge initialized for topics: {self.bridge_topics}")
        
        except Exception as e:
            logger.error(f"Failed to initialize bridge consumer: {e}")
            self.enabled = False
    
    async def start(self):
        """Start bridging loop"""
        if not self.enabled or not self.consumer:
            logger.info("Kafka-WebSocket bridge disabled")
            return
        
        self.running = True
        logger.info("Starting Kafka-WebSocket bridge...")
        
        while self.running:
            try:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Bridge consumer error: {msg.error()}")
                        continue
                
                # Process message
                await self._process_message(msg)
            
            except Exception as e:
                logger.error(f"Error in bridge loop: {e}")
                await asyncio.sleep(1)
        
        logger.info("Kafka-WebSocket bridge stopped")
    
    async def _process_message(self, msg):
        """Process Kafka message and broadcast to WebSocket"""
        try:
            topic = msg.topic()
            key = msg.key().decode('utf-8') if msg.key() else None
            value = json.loads(msg.value().decode('utf-8'))
            
            # Route based on topic
            if topic == "alerts":
                await self._handle_alert(value)
            
            elif topic == "trace.progress":
                await self._handle_trace_progress(value, key)
            
            elif topic == "bridge.detected":
                await self._handle_bridge_detected(value)
            
            elif topic == "enrichment.completed":
                await self._handle_enrichment(value)
            
            else:
                # Generic broadcast
                await manager.broadcast({
                    "type": "kafka_event",
                    "topic": topic,
                    "data": value
                })
        
        except Exception as e:
            logger.error(f"Error processing bridge message: {e}")
    
    async def _handle_alert(self, data: Dict):
        """Handle alert event"""
        await manager.send_alert({
            "alert_type": data.get("alert_type"),
            "severity": data.get("severity"),
            "message": data.get("message"),
            "metadata": data.get("metadata"),
            "timestamp": data.get("timestamp")
        })
    
    async def _handle_trace_progress(self, data: Dict, trace_id: Optional[str]):
        """Handle trace progress update"""
        if trace_id:
            await manager.send_trace_update(trace_id, {
                "status": data.get("status"),
                "progress": data.get("progress"),
                "nodes_found": data.get("nodes_found"),
                "current_hop": data.get("current_hop"),
                "message": data.get("message")
            })
    
    async def _handle_bridge_detected(self, data: Dict):
        """Handle bridge detection event"""
        await manager.broadcast({
            "type": "bridge_detected",
            "data": {
                "bridge_name": data.get("bridge_name"),
                "chain_from": data.get("chain_from"),
                "chain_to": data.get("chain_to"),
                "tx_hash": data.get("tx_hash"),
                "from_address": data.get("from_address"),
                "to_address": data.get("to_address")
            }
        })
    
    async def _handle_enrichment(self, data: Dict):
        """Handle enrichment completion"""
        await manager.broadcast({
            "type": "enrichment_completed",
            "data": {
                "address": data.get("address"),
                "labels": data.get("labels"),
                "risk_score": data.get("risk_score"),
                "is_sanctioned": data.get("is_sanctioned")
            }
        })
    
    def stop(self):
        """Stop bridge"""
        logger.info("Stopping Kafka-WebSocket bridge...")
        self.running = False
        
        if self.consumer:
            self.consumer.close()


# Global bridge instance
kafka_ws_bridge = KafkaWebSocketBridge()


# Background task runner
async def start_kafka_bridge():
    """Start bridge as background task"""
    await kafka_ws_bridge.start()
