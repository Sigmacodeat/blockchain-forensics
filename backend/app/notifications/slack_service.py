"""
Slack Notification Service
Real-time alerts to Slack channels
"""

import logging
from typing import Dict
import json

logger = logging.getLogger(__name__)


class SlackService:
    """
    Slack notification service
    
    **Use Cases:**
    - Team alerts for high-risk detections
    - Real-time sanctions notifications
    - System health alerts
    
    **Setup:**
    - Create Slack Webhook URL
    - Add SLACK_WEBHOOK_URL to .env
    """
    
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        logger.info(f"Slack service initialized ({'enabled' if self.enabled else 'disabled'})")
    
    async def send_message(self, text: str, attachments: list = None):
        """
        Send message to Slack
        
        Args:
            text: Message text
            attachments: Optional attachments
        """
        if not self.enabled:
            logger.info(f"Slack disabled. Would send: {text}")
            return
        
        payload = {
            "text": text,
            "attachments": attachments or []
        }
        
        # Actual HTTP POST to Slack webhook
        if self.enabled and self.webhook_url:
            try:
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            logger.info(f"Slack message sent: {text[:50]}...")
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(f"Slack error {response.status}: {error_text}")
                            return False
            
            except Exception as e:
                logger.error(f"Slack POST failed: {e}")
                return False
        else:
            # Development mode - just log
            logger.info(f"[DEV] Would POST to Slack: {text}")
    
    async def alert_high_risk(self, address: str, risk_score: float):
        """Send high-risk alert to Slack"""
        text = f"⚠️ *High-Risk Address Detected*\n`{address}`\nRisk Score: {risk_score * 100:.1f}%"
        
        attachments = [
            {
                "color": "warning",
                "fields": [
                    {"title": "Address", "value": address, "short": False},
                    {"title": "Risk Score", "value": f"{risk_score * 100:.1f}%", "short": True}
                ]
            }
        ]
        
        await self.send_message(text, attachments)
    
    async def alert_sanctions(self, address: str):
        """Send sanctions alert to Slack"""
        text = f"🚨 *SANCTIONED ENTITY DETECTED*\n`{address}`\n<!channel> IMMEDIATE ACTION REQUIRED"
        
        attachments = [
            {
                "color": "danger",
                "fields": [
                    {"title": "Address", "value": address, "short": False},
                    {"title": "Action", "value": "Review immediately", "short": True}
                ]
            }
        ]
        
        await self.send_message(text, attachments)


# Singleton (configure with webhook URL from settings)
slack_service = SlackService()
