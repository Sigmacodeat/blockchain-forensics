"""
Support Service - KI-gestütztes Ticket-System mit Auto-Reply
"""
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from app.config import settings
from app.db.postgres_client import postgres_client

logger = logging.getLogger(__name__)


class SupportService:
    """Support-Service für Kontaktformulare und Tickets"""
    
    def __init__(self):
        self.email_service = None
        
    async def submit_contact_form(
        self,
        name: str,
        email: str,
        subject: str,
        message: str,
        country: Optional[str] = None,
        language: Optional[str] = "en",
        user_id: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        referrer: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit contact form / support ticket"""
        try:
            ticket_id = str(uuid.uuid4())[:8].upper()
            priority = await self._classify_priority(subject, message)
            category = await self._detect_category(subject, message)
            ai_reply = await self._generate_ai_reply(subject, message, language, category)
            
            ticket_data = {
                "ticket_id": ticket_id,
                "name": name,
                "email": email,
                "subject": subject,
                "message": message,
                "country": country,
                "language": language,
                "user_id": user_id,
                "user_agent": user_agent,
                "ip_address": ip_address,
                "referrer": referrer,
                "priority": priority,
                "category": category,
                "status": "open",
                "ai_reply": ai_reply,
                "metadata": json.dumps(metadata or {}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await self._save_ticket(ticket_data)
            await self._send_confirmation_email(email, name, ticket_id, subject, language, ai_reply)
            await self._notify_support_team(ticket_data)
            
            logger.info(f"Ticket created: {ticket_id} | Priority: {priority} | Country: {country}")
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "priority": priority,
                "category": category,
                "ai_reply": ai_reply,
                "estimated_response_time": self._get_estimated_response_time(priority)
            }
            
        except Exception as e:
            logger.error(f"Error submitting contact form: {e}")
            return {"success": False, "error": str(e)}
    
    async def _classify_priority(self, subject: str, message: str) -> str:
        """Classify ticket priority"""
        text = f"{subject} {message}".lower()
        critical = ["hack", "stolen", "fraud", "urgent", "critical", "notfall", "dringend"]
        high = ["bug", "error", "broken", "payment issue", "fehler", "problem"]
        
        for keyword in critical:
            if keyword in text:
                return "critical"
        for keyword in high:
            if keyword in text:
                return "high"
        return "medium" if "?" in text else "low"
    
    async def _detect_category(self, subject: str, message: str) -> str:
        """Detect support category"""
        text = f"{subject} {message}".lower()
        if any(w in text for w in ["bug", "error", "crash", "fehler"]): return "technical"
        if any(w in text for w in ["payment", "invoice", "billing", "zahlung"]): return "billing"
        if any(w in text for w in ["price", "plan", "upgrade", "demo"]): return "sales"
        if any(w in text for w in ["feature", "request", "suggestion"]): return "feature_request"
        return "general"
    
    async def _generate_ai_reply(self, subject: str, message: str, lang: str, category: str) -> Optional[str]:
        """Generate AI auto-reply"""
        templates = {
            "technical": {
                "en": "Thank you for reporting this issue. Our team will investigate within 24 hours.",
                "de": "Vielen Dank für die Meldung. Unser Team wird das innerhalb von 24 Stunden untersuchen.",
            },
            "billing": {
                "en": "Thank you for contacting us about billing. We'll review and respond within 24 hours.",
                "de": "Vielen Dank für Ihre Anfrage zur Abrechnung. Wir prüfen und antworten innerhalb von 24 Stunden.",
            },
            "sales": {
                "en": "Thank you for your interest! Our sales team will reach out within 12 hours.",
                "de": "Vielen Dank für Ihr Interesse! Unser Vertrieb meldet sich innerhalb von 12 Stunden.",
            },
            "general": {
                "en": "Thank you for contacting us. We'll respond within 24-48 hours.",
                "de": "Vielen Dank für Ihre Nachricht. Wir antworten innerhalb von 24-48 Stunden.",
            }
        }
        return templates.get(category, templates["general"]).get(lang, templates[category]["en"])
    
    def _get_estimated_response_time(self, priority: str) -> str:
        times = {"critical": "1-2 hours", "high": "4-8 hours", "medium": "24 hours", "low": "24-48 hours"}
        return times.get(priority, "24-48 hours")
    
    async def _save_ticket(self, data: Dict[str, Any]) -> None:
        """Save ticket to PostgreSQL"""
        query = """
        INSERT INTO support_tickets (
            ticket_id, name, email, subject, message, country, language,
            user_id, user_agent, ip_address, referrer, priority, category,
            status, ai_reply, metadata, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        """
        await postgres_client.execute(query, *[data[k] for k in [
            "ticket_id", "name", "email", "subject", "message", "country", "language",
            "user_id", "user_agent", "ip_address", "referrer", "priority", "category",
            "status", "ai_reply", "metadata", "created_at", "updated_at"
        ]])
    
    async def _send_confirmation_email(self, to_email: str, name: str, ticket_id: str, 
                                      subject: str, lang: str, ai_reply: Optional[str]) -> None:
        """Send confirmation email"""
        if not self.email_service:
            from app.services.email_notifications import email_service
            self.email_service = email_service
        
        if not self.email_service.enabled:
            return
        
        t = {"en": {"title": "Support Request Received", "body": f"Hello {name}! We've received your request #{ticket_id}."},
             "de": {"title": "Support-Anfrage erhalten", "body": f"Hallo {name}! Wir haben Ihre Anfrage #{ticket_id} erhalten."}}
        
        trans = t.get(lang, t["en"])
        html = f"""<html><body style="font-family:Arial;padding:20px;"><h2>✅ {trans['title']}</h2><p>{trans['body']}</p>
        <div style="background:#f0f0f0;padding:15px;margin:20px 0;"><strong>Ticket:</strong> #{ticket_id}<br><strong>Subject:</strong> {subject}</div>
        {f'<div style="background:#e0e7ff;padding:15px;"><strong>🤖 Auto-Reply:</strong><p>{ai_reply}</p></div>' if ai_reply else ''}
        <p style="color:#666;font-size:12px;">SIGMACODE Blockchain Forensics | support@blockchain-forensics.com</p></body></html>"""
        
        await self.email_service._send_email(to_email, f"✅ {trans['title']} - #{ticket_id}", html)
    
    async def _notify_support_team(self, data: Dict[str, Any]) -> None:
        """Notify support team"""
        if not self.email_service:
            from app.services.email_notifications import email_service
            self.email_service = email_service
        
        if not self.email_service.enabled:
            return
        
        support_email = settings.SUPPORT_EMAIL or "support@blockchain-forensics.com"
        emoji = {"critical": "🚨", "high": "⚠️", "medium": "📌", "low": "📝"}.get(data['priority'], '📧')
        
        html = f"""<html><body style="font-family:Arial;padding:20px;"><h2>{emoji} New Ticket #{data['ticket_id']}</h2>
        <div style="background:#f0f0f0;padding:15px;"><strong>From:</strong> {data['name']} ({data['email']})<br>
        <strong>Subject:</strong> {data['subject']}<br><strong>Priority:</strong> {data['priority'].upper()}<br>
        <strong>Category:</strong> {data['category']}<br><strong>Country:</strong> {data['country'] or 'Unknown'}<br>
        <strong>Language:</strong> {data['language']}<br><strong>Message:</strong><p>{data['message']}</p></div>
        {f"<div style='background:#e0e7ff;padding:15px;'><strong>🤖 AI Reply:</strong><p>{data['ai_reply']}</p></div>" if data['ai_reply'] else ''}
        <p><a href="{settings.FRONTEND_URL}/admin/support?ticket={data['ticket_id']}">View in Admin Dashboard</a></p></body></html>"""
        
        await self.email_service._send_email(support_email, f"{emoji} New Ticket #{data['ticket_id']} - {data['priority'].upper()}", html)
    
    async def list_tickets(self, status: Optional[str] = None, priority: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List tickets with filters"""
        conditions = []
        params = []
        if status:
            conditions.append(f"status = ${len(params) + 1}")
            params.append(status)
        if priority:
            conditions.append(f"priority = ${len(params) + 1}")
            params.append(priority)
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM support_tickets {where} ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        rows = await postgres_client.fetch(query, *params)
        return [dict(row) for row in rows]


support_service = SupportService()
