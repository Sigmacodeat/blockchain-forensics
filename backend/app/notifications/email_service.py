"""
Email Notification Service
Alert notifications via Email
"""

import logging
from typing import List
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email notification service
    
    **Use Cases:**
    - High-risk address alerts
    - OFAC sanctions notifications
    - Trace completion reports
    - System alerts
    
    **TODO:**
    - Install: pip install python-smtp
    - Configure SMTP settings
    """
    
    def __init__(self):
        # Enable via settings
        try:
            self.enabled = bool(getattr(settings, "EMAIL_ENABLED", False))
        except Exception:
            self.enabled = False
        logger.info(f"Email service initialized (enabled={self.enabled})")
    
    async def send_high_risk_alert(
        self,
        recipient: str,
        address: str,
        risk_score: float,
        factors: List[str]
    ):
        """
        Send high-risk address alert
        
        Args:
            recipient: Email address
            address: Ethereum address
            risk_score: Risk score (0-1)
            factors: Risk factors
        """
        subject = f"⚠️ High-Risk Address Detected: {address[:10]}..."
        body = f"""
High-Risk Address Alert

Address: {address}
Risk Score: {risk_score * 100:.1f}%
Detected: {datetime.utcnow().isoformat()}

Risk Factors:
{chr(10).join(f'- {f}' for f in factors)}

Please review this address immediately in the platform.
        """

        if not self.enabled or not getattr(settings, "EMAIL_ENABLED", False):
            logger.info(f"[DEV] Email disabled. Would send high-risk alert to {recipient}: {subject}")
            return

        # Build simple HTML from text body
        html_content = f"<pre>{body}</pre>"

        # Actual email sending implementation
        try:
            backend = getattr(settings, "EMAIL_BACKEND", "smtp")
            if backend == "sendgrid":
                await self._send_via_sendgrid(recipient, subject, html_content)
            elif backend == "smtp":
                await self._send_via_smtp(recipient, subject, html_content)
            else:
                logger.warning(f"Unknown email backend: {backend}")
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise
    
    async def send_sanctions_alert(
        self,
        recipient: str,
        address: str,
        sanction_list: str
    ):
        """Send OFAC sanctions alert"""
        subject = f"🚨 SANCTIONED ENTITY DETECTED: {address[:10]}..."
        body = f"""
CRITICAL: OFAC Sanctioned Entity Detected

Address: {address}
Sanction List: {sanction_list}
Detected: {datetime.utcnow().isoformat()}

IMMEDIATE ACTION REQUIRED

This address is on OFAC sanctions lists. Any interaction
with this address may be illegal. Please escalate immediately.
        """

        if not self.enabled or not getattr(settings, "EMAIL_ENABLED", False):
            logger.warning(f"[DEV] Email disabled. Would send SANCTIONS alert to {recipient}: {subject}")
            return

        html_content = f"<pre>{body}</pre>"
        try:
            backend = getattr(settings, "EMAIL_BACKEND", "smtp")
            if backend == "sendgrid":
                await self._send_via_sendgrid(recipient, subject, html_content)
            elif backend == "smtp":
                await self._send_via_smtp(recipient, subject, html_content)
            else:
                logger.warning(f"Unknown email backend: {backend}")
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise
    
    async def send_trace_complete(
        self,
        recipient: str,
        trace_id: str,
        total_nodes: int,
        high_risk_count: int
    ):
        """Send trace completion notification"""
        if not self.enabled:
            return
        
        subject = f"✓ Trace Complete: {trace_id}"
        body = f"""
Blockchain Trace Completed

Trace ID: {trace_id}
Total Nodes: {total_nodes}
High-Risk Addresses: {high_risk_count}
Completed: {datetime.utcnow().isoformat()}

View results: https://platform.example.com/trace/{trace_id}
        """
        
        logger.info(f"Would send trace completion: {subject}")


    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str):
        """Send email via SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            
            logger.info(f"SendGrid email sent: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            raise
    
    async def _send_via_smtp(self, to_email: str, subject: str, html_content: str):
        """Send email via SMTP"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(msg)
            
            logger.info(f"SMTP email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise


# Singleton instance
email_service = EmailService()
