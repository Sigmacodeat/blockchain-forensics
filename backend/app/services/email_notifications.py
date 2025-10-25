"""
Email Notification Service for Crypto Payments
Sends notifications for payment events
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Email notification service for crypto payment events
    Supports multiple backends: SMTP, SendGrid
    """
    
    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.backend = settings.EMAIL_BACKEND
        self.from_email = settings.EMAIL_FROM
        
    async def send_payment_created(
        self,
        user_email: str,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Send email when payment is created
        
        Args:
            user_email: User's email address
            payment_data: Payment information
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.info("Email notifications disabled, skipping")
            return False
        
        try:
            subject = f"💎 Krypto-Zahlung erstellt - {payment_data['pay_currency'].upper()}"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .payment-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                    .amount {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                    .address {{ font-family: monospace; background: #f3f4f6; padding: 10px; border-radius: 4px; word-break: break-all; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>💎 Krypto-Zahlung erstellt</h1>
                        <p>Ihre {payment_data['plan_name'].title()} Subscription</p>
                    </div>
                    <div class="content">
                        <p>Hallo!</p>
                        <p>Ihre Krypto-Zahlung wurde erfolgreich erstellt. Bitte senden Sie den exakten Betrag an die angegebene Adresse:</p>
                        
                        <div class="payment-box">
                            <p><strong>Zu zahlender Betrag:</strong></p>
                            <div class="amount">{payment_data['pay_amount']} {payment_data['pay_currency'].upper()}</div>
                            <p style="color: #6b7280; font-size: 14px;">≈ ${payment_data['price_amount']} USD</p>
                            
                            <p style="margin-top: 20px;"><strong>Zahlungsadresse:</strong></p>
                            <div class="address">{payment_data['pay_address']}</div>
                            
                            <p style="margin-top: 20px;"><strong>Gültigkeit:</strong></p>
                            <p style="color: #ef4444;">Zahlung läuft in 15 Minuten ab!</p>
                        </div>
                        
                        <div class="warning">
                            <strong>⚠️ Wichtig:</strong> Bitte senden Sie <strong>nur {payment_data['pay_currency'].upper()}</strong> an diese Adresse. 
                            Das Senden anderer Kryptowährungen führt zu einem permanenten Verlust!
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{payment_data.get('invoice_url', '#')}" class="button">
                                Zahlung abschließen
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px;">
                            Nach erfolgreicher Zahlung wird Ihr <strong>{payment_data['plan_name'].title()}</strong> Plan automatisch aktiviert.
                        </p>
                        
                        <div class="footer">
                            <p>SIGMACODE Blockchain Forensics Platform</p>
                            <p>Bei Fragen: support@blockchain-forensics.com</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(user_email, subject, html_body)
        except Exception as e:
            logger.error(f"Error sending payment created email: {e}")
            return False
    
    async def send_payment_success(
        self,
        user_email: str,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Send email when payment is successful
        
        Args:
            user_email: User's email address
            payment_data: Payment information
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            subject = f"✅ Zahlung erfolgreich - {payment_data['plan_name'].title()} aktiviert!"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .success-box {{ background: #d1fae5; border-left: 4px solid #10b981; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                    .button {{ display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Zahlung erfolgreich!</h1>
                        <p>Willkommen bei {payment_data['plan_name'].title()}</p>
                    </div>
                    <div class="content">
                        <div class="success-box">
                            <h2 style="margin-top: 0; color: #059669;">✓ Payment Received</h2>
                            <p>Ihre Krypto-Zahlung wurde erfolgreich verarbeitet und Ihr Plan wurde aktiviert!</p>
                        </div>
                        
                        <div class="details">
                            <h3>Zahlungsdetails</h3>
                            <div class="detail-row">
                                <span>Plan:</span>
                                <strong>{payment_data['plan_name'].title()}</strong>
                            </div>
                            <div class="detail-row">
                                <span>Betrag:</span>
                                <strong>{payment_data.get('actual_pay_amount', payment_data['pay_amount'])} {payment_data['pay_currency'].upper()}</strong>
                            </div>
                            <div class="detail-row">
                                <span>Transaktions-Hash:</span>
                                <span style="font-family: monospace; font-size: 12px;">{payment_data.get('pay_in_hash', 'N/A')[:16]}...</span>
                            </div>
                            <div class="detail-row">
                                <span>Datum:</span>
                                <strong>{datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC</strong>
                            </div>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{settings.FRONTEND_URL}/dashboard" class="button">
                                Zum Dashboard
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px;">
                            Sie können jetzt alle Features Ihres <strong>{payment_data['plan_name'].title()}</strong> Plans nutzen!
                        </p>
                        
                        <div class="footer">
                            <p>SIGMACODE Blockchain Forensics Platform</p>
                            <p>Bei Fragen: support@blockchain-forensics.com</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(user_email, subject, html_body)
        except Exception as e:
            logger.error(f"Error sending payment success email: {e}")
            return False
    
    async def send_payment_failed(
        self,
        user_email: str,
        payment_data: Dict[str, Any],
        reason: str
    ) -> bool:
        """
        Send email when payment fails
        
        Args:
            user_email: User's email address
            payment_data: Payment information
            reason: Failure reason
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            subject = f"❌ Zahlung fehlgeschlagen - {payment_data['plan_name'].title()}"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .error-box {{ background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>❌ Zahlung fehlgeschlagen</h1>
                    </div>
                    <div class="content">
                        <div class="error-box">
                            <h3 style="margin-top: 0; color: #dc2626;">Payment Failed</h3>
                            <p><strong>Grund:</strong> {reason}</p>
                        </div>
                        
                        <p>Ihre Zahlung für den <strong>{payment_data['plan_name'].title()}</strong> Plan konnte leider nicht verarbeitet werden.</p>
                        
                        <p><strong>Mögliche Ursachen:</strong></p>
                        <ul>
                            <li>Zahlungsbetrag war nicht korrekt</li>
                            <li>Zahlung wurde zu spät gesendet (Timeout)</li>
                            <li>Falsche Kryptowährung gesendet</li>
                        </ul>
                        
                        <div style="text-align: center;">
                            <a href="{settings.FRONTEND_URL}/pricing" class="button">
                                Erneut versuchen
                            </a>
                        </div>
                        
                        <p style="margin-top: 30px;">
                            Bei Fragen kontaktieren Sie bitte unseren Support.
                        </p>
                        
                        <div class="footer">
                            <p>SIGMACODE Blockchain Forensics Platform</p>
                            <p>Support: support@blockchain-forensics.com</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return await self._send_email(user_email, subject, html_body)
        except Exception as e:
            logger.error(f"Error sending payment failed email: {e}")
            return False
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str
    ) -> bool:
        """
        Send email via configured backend
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            
        Returns:
            True if sent successfully
        """
        try:
            if self.backend == "sendgrid":
                return await self._send_via_sendgrid(to_email, subject, html_body)
            elif self.backend == "smtp":
                return await self._send_via_smtp(to_email, subject, html_body)
            else:
                logger.warning(f"Unknown email backend: {self.backend}")
                return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str
    ) -> bool:
        """Send email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_body
            )
            response = sg.send(message)
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str
    ) -> bool:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False


# Singleton instance
email_service = EmailNotificationService()
