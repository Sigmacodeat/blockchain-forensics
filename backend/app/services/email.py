"""
Email Service
Send verification, password reset, and notification emails
"""

import logging
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.config import settings

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Email message model"""
    to: EmailStr
    subject: str
    html_body: str
    text_body: Optional[str] = None


class EmailService:
    """
    Email Service for sending transactional emails
    
    **In Production:**
    - Use SendGrid, AWS SES, or similar
    - Configure SMTP settings
    - Add email templates
    
    **Current Implementation:**
    - Logs emails to console (dev mode)
    - No actual emails sent
    """
    
    def __init__(self):
        self.enabled = False  # Set to True when email provider is configured
        self.from_email = "noreply@blockchain-forensics.com"
        self.from_name = "Blockchain Forensics Platform"
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send email using configured backend, fallback to logging in dev mode"""
        # Enable flag can be overridden by settings
        try:
            self.enabled = bool(getattr(settings, "EMAIL_ENABLED", False))
        except Exception:
            pass
        if not self.enabled:
            logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ 📧 EMAIL (DEV MODE - NOT SENT)                                 ║
╠════════════════════════════════════════════════════════════════╣
║ To: {message.to:<58} ║
║ Subject: {message.subject:<53} ║
╠════════════════════════════════════════════════════════════════╣
║ {message.html_body[:60]:<62} ║
╚════════════════════════════════════════════════════════════════╝
            """)
            return True

        # Send via configured backend
        try:
            backend = getattr(settings, "EMAIL_BACKEND", "smtp")
            if backend == "sendgrid":
                try:
                    from sendgrid import SendGridAPIClient  # type: ignore
                    from sendgrid.helpers.mail import Mail  # type: ignore
                except Exception as e:
                    logger.error(f"SendGrid import error: {e}")
                    return False
                mail = Mail(
                    from_email=self.from_email,
                    to_emails=str(message.to),
                    subject=message.subject,
                    html_content=message.html_body,
                )
                try:
                    sg = SendGridAPIClient(getattr(settings, "SENDGRID_API_KEY", ""))
                    response = sg.send(mail)
                    return getattr(response, "status_code", 0) in (200, 202)
                except Exception as e:
                    logger.error(f"Failed to send email via SendGrid: {e}")
                    return False
            elif backend == "smtp":
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                except Exception as e:
                    logger.error(f"SMTP import error: {e}")
                    return False
                msg = MIMEMultipart('alternative')
                msg['Subject'] = message.subject
                msg['From'] = self.from_email
                msg['To'] = str(message.to)
                html_part = MIMEText(message.html_body, 'html')
                msg.attach(html_part)
                try:
                    host = getattr(settings, "SMTP_HOST", "localhost")
                    port = int(getattr(settings, "SMTP_PORT", 25))
                    use_tls = bool(getattr(settings, "SMTP_USE_TLS", False))
                    user = getattr(settings, "SMTP_USER", "")
                    password = getattr(settings, "SMTP_PASSWORD", "")
                    with smtplib.SMTP(host, port, timeout=15) as server:
                        if use_tls:
                            try:
                                server.starttls()
                            except Exception:
                                pass
                        if user and password:
                            server.login(user, password)
                        server.send_message(msg)
                    return True
                except Exception as e:
                    logger.error(f"Failed to send email via SMTP: {e}")
                    return False
            else:
                logger.warning(f"Unknown email backend: {backend}. Falling back to dev log.")
                return False
        except Exception as e:
            logger.error(f"Email sending unexpected error: {e}")
            return False
    
    async def send_verification_email(self, to: str, username: str, token: str) -> bool:
        """Send email verification"""
        verification_link = f"http://localhost:3000/verify-email?token={token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Blockchain Forensics</h1>
                </div>
                <div class="content">
                    <h2>Willkommen, {username}!</h2>
                    <p>Vielen Dank für deine Registrierung bei Blockchain Forensics Platform.</p>
                    <p>Bitte bestätige deine E-Mail-Adresse, um deinen Account zu aktivieren:</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">E-Mail bestätigen</a>
                    </p>
                    <p>Oder kopiere diesen Link in deinen Browser:</p>
                    <p style="word-break: break-all; background: white; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;">
                        {verification_link}
                    </p>
                    <p><strong>Dieser Link ist 24 Stunden gültig.</strong></p>
                    <p>Falls du dich nicht registriert hast, ignoriere diese E-Mail.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Blockchain Forensics Platform</p>
                    <p>Diese E-Mail wurde automatisch generiert.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = EmailMessage(
            to=to,
            subject="E-Mail-Adresse bestätigen",
            html_body=html_body
        )
        
        return await self.send_email(message)
    
    async def send_password_reset_email(self, to: str, username: str, token: str) -> bool:
        """Send password reset email"""
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Passwort zurücksetzen</h1>
                </div>
                <div class="content">
                    <h2>Hallo, {username}!</h2>
                    <p>Wir haben eine Anfrage zum Zurücksetzen deines Passworts erhalten.</p>
                    <p>Klicke auf den Button, um ein neues Passwort festzulegen:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Passwort zurücksetzen</a>
                    </p>
                    <p>Oder kopiere diesen Link in deinen Browser:</p>
                    <p style="word-break: break-all; background: white; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px;">
                        {reset_link}
                    </p>
                    <div class="warning">
                        <strong>⚠️ Sicherheitshinweis:</strong><br>
                        • Dieser Link ist 1 Stunde gültig<br>
                        • Falls du diese Anfrage nicht gestellt hast, ignoriere diese E-Mail<br>
                        • Dein Passwort wurde noch nicht geändert
                    </div>
                </div>
                <div class="footer">
                    <p>© 2025 Blockchain Forensics Platform</p>
                    <p>Diese E-Mail wurde automatisch generiert.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = EmailMessage(
            to=to,
            subject="Passwort zurücksetzen",
            html_body=html_body
        )
        
        return await self.send_email(message)
    
    async def send_welcome_email(self, to: str, username: str) -> bool:
        """Send welcome email after verification"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .features {{ background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Account aktiviert!</h1>
                </div>
                <div class="content">
                    <h2>Willkommen, {username}!</h2>
                    <p>Dein Account wurde erfolgreich verifiziert. Du kannst jetzt alle Features nutzen:</p>
                    <div class="features">
                        <h3>🔍 Verfügbare Features:</h3>
                        <ul>
                            <li><strong>Transaction Tracing:</strong> Rekursives N-Hop-Tracing mit Taint-Modellen</li>
                            <li><strong>AI Forensic Agent:</strong> Autonome forensische Analyse</li>
                            <li><strong>Risk Scoring:</strong> ML-basierte Risikobewertung</li>
                            <li><strong>Reports:</strong> Gerichtsverwertbare PDF-Reports</li>
                        </ul>
                    </div>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="http://localhost:3000/login" style="display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                            Jetzt anmelden
                        </a>
                    </p>
                    <p>Bei Fragen oder Problemen, kontaktiere uns gerne.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Blockchain Forensics Platform</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = EmailMessage(
            to=to,
            subject="Account erfolgreich aktiviert! 🎉",
            html_body=html_body
        )
        
        return await self.send_email(message)


# Singleton instance
email_service = EmailService()
