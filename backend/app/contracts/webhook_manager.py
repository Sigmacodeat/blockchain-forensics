"""
Webhook & Notification Manager
===============================
Sends real-time notifications for contract events.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Webhook configuration"""
    url: str
    events: List[str]  # ["critical_finding", "proxy_upgrade", "risk_spike"]
    secret: Optional[str] = None
    enabled: bool = True


class WebhookManager:
    """
    Manages webhooks for contract analysis events.
    
    Supported Events:
    - critical_finding: Critical vulnerability detected
    - high_risk: Risk score > 0.7
    - proxy_upgrade: Proxy implementation changed
    - risk_spike: Risk increased > 0.3
    """
    
    def __init__(self):
        self._webhooks: Dict[str, List[WebhookConfig]] = {}
    
    def register_webhook(
        self,
        address: str,
        chain: str,
        config: WebhookConfig
    ):
        """Register webhook for contract"""
        key = f"{chain}:{address}".lower()
        if key not in self._webhooks:
            self._webhooks[key] = []
        
        self._webhooks[key].append(config)
    
    def unregister_webhook(
        self,
        address: str,
        chain: str,
        url: str
    ):
        """Unregister webhook"""
        key = f"{chain}:{address}".lower()
        if key in self._webhooks:
            self._webhooks[key] = [
                w for w in self._webhooks[key]
                if w.url != url
            ]
    
    async def trigger_event(
        self,
        address: str,
        chain: str,
        event_type: str,
        data: Dict
    ):
        """Trigger webhook event"""
        key = f"{chain}:{address}".lower()
        if key not in self._webhooks:
            return
        
        # Filter webhooks interested in this event
        relevant_webhooks = [
            w for w in self._webhooks[key]
            if w.enabled and event_type in w.events
        ]
        
        if not relevant_webhooks:
            return
        
        # Send to all webhooks in parallel
        tasks = [
            self._send_webhook(webhook, event_type, data)
            for webhook in relevant_webhooks
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_webhook(
        self,
        webhook: WebhookConfig,
        event_type: str,
        data: Dict
    ):
        """Send webhook HTTP POST"""
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": data.get("timestamp"),
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BlockchainForensics/1.0",
        }
        
        if webhook.secret:
            # In production, add HMAC signature
            headers["X-Webhook-Secret"] = webhook.secret
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook sent to {webhook.url}: {event_type}")
        except Exception as e:
            logger.error(f"Webhook failed {webhook.url}: {e}")
    
    async def check_and_trigger_events(
        self,
        address: str,
        chain: str,
        analysis: Dict,
        previous_analysis: Optional[Dict] = None
    ):
        """Check analysis for events and trigger webhooks"""
        from datetime import datetime
        
        timestamp = datetime.utcnow().isoformat()
        
        # Critical Finding
        critical_count = analysis.get("vulnerabilities", {}).get("critical", 0)
        if critical_count > 0:
            await self.trigger_event(
                address, chain, "critical_finding",
                {
                    "address": address,
                    "chain": chain,
                    "critical_count": critical_count,
                    "score": analysis.get("score", 0),
                    "timestamp": timestamp,
                }
            )
        
        # High Risk
        if analysis.get("score", 0) > 0.7:
            await self.trigger_event(
                address, chain, "high_risk",
                {
                    "address": address,
                    "chain": chain,
                    "score": analysis.get("score", 0),
                    "timestamp": timestamp,
                }
            )
        
        # Proxy Upgrade (if previous analysis available)
        if previous_analysis:
            prev_impl = previous_analysis.get("proxy", {}).get("implementation")
            curr_impl = analysis.get("proxy", {}).get("implementation")
            
            if prev_impl and curr_impl and prev_impl != curr_impl:
                await self.trigger_event(
                    address, chain, "proxy_upgrade",
                    {
                        "address": address,
                        "chain": chain,
                        "from_implementation": prev_impl,
                        "to_implementation": curr_impl,
                        "timestamp": timestamp,
                    }
                )
            
            # Risk Spike
            prev_score = previous_analysis.get("score", 0)
            curr_score = analysis.get("score", 0)
            
            if curr_score > prev_score + 0.3:
                await self.trigger_event(
                    address, chain, "risk_spike",
                    {
                        "address": address,
                        "chain": chain,
                        "previous_score": prev_score,
                        "current_score": curr_score,
                        "delta": curr_score - prev_score,
                        "timestamp": timestamp,
                    }
                )


# Singleton
webhook_manager = WebhookManager()
