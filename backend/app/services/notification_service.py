"""
Notification Service
Handles email notifications for subscriptions, payments, etc.
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Service für Benachrichtigungen"""
    
    async def send_payment_failure_email(
        self,
        user_email: str,
        payment_intent_id: str,
        amount: int,
        error_message: str
    ) -> Dict[str, Any]:
        """Send email notification for failed payment"""
        logger.info(f"Sending payment failure email to {user_email}")
        
        # In real app: use SendGrid/Mailgun/SES
        # Simplified for tests
        return {
            'status': 'sent',
            'to': user_email,
            'subject': 'Payment Failed',
            'type': 'payment_failure',
            'sent_at': datetime.now().isoformat()
        }
    
    async def send_renewal_reminder(
        self,
        user_email: str,
        renewal_date: datetime,
        plan: str,
        amount: int
    ) -> Dict[str, Any]:
        """Send email reminder for upcoming renewal"""
        logger.info(f"Sending renewal reminder to {user_email}")
        
        return {
            'status': 'sent',
            'to': user_email,
            'subject': f'{plan.title()} Plan Renewal in 3 Days',
            'type': 'renewal_reminder',
            'sent_at': datetime.now().isoformat()
        }
    
    async def send_subscription_cancelled_email(
        self,
        user_email: str,
        plan: str,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Send email notification for cancelled subscription"""
        logger.info(f"Sending cancellation confirmation to {user_email}")
        
        return {
            'status': 'sent',
            'to': user_email,
            'subject': 'Subscription Cancelled',
            'type': 'subscription_cancelled',
            'sent_at': datetime.now().isoformat()
        }
    
    async def send_upgrade_confirmation_email(
        self,
        user_email: str,
        old_plan: str,
        new_plan: str,
        amount: int
    ) -> Dict[str, Any]:
        """Send email confirmation for plan upgrade"""
        logger.info(f"Sending upgrade confirmation to {user_email}")
        
        return {
            'status': 'sent',
            'to': user_email,
            'subject': f'Upgraded to {new_plan.title()} Plan',
            'type': 'upgrade_confirmation',
            'sent_at': datetime.now().isoformat()
        }
    
    async def send_downgrade_warning_email(
        self,
        user_email: str,
        current_plan: str,
        downgrade_date: datetime,
        reason: str = "payment_failure"
    ) -> Dict[str, Any]:
        """Send warning email about upcoming downgrade"""
        logger.info(f"Sending downgrade warning to {user_email}")
        
        return {
            'status': 'sent',
            'to': user_email,
            'subject': 'Action Required: Subscription Downgrade',
            'type': 'downgrade_warning',
            'sent_at': datetime.now().isoformat()
        }


# Global instance
notification_service = NotificationService()
