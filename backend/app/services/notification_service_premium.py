"""
Premium Notification Service
Enterprise-grade notifications with multiple channels and preferences
"""

import logging
import json
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.user import UserORM, User
from app.models.notification import (
    Notification, NotificationSettings, NotificationTemplate,
    NotificationType, NotificationPriority, NotificationChannel,
    create_notification, get_notification, mark_notification_read,
    mark_all_notifications_read, delete_notification, query_notifications,
    get_user_notification_settings, update_notification_settings,
    create_notification_template, get_notification_template, render_notification_template,
    get_unread_count, NotificationQuery
)
from app.notifications.email_service import email_service
import os

logger = logging.getLogger(__name__)


# ===================================
# IN-APP NOTIFICATION MODEL
# ===================================

class InAppNotification:
    """Model for in-app notifications (stored in DB)"""
    
    def __init__(
        self,
        user_id: int,
        title: str,
        message: str,
        type: str,
        priority: str = 'normal',
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = type  # 'alert', 'trace_complete', 'case_update', 'payment', 'system'
        self.priority = priority  # 'low', 'normal', 'high', 'critical'
        self.action_url = action_url
        self.metadata = metadata or {}
        self.read = False
        self.created_at = datetime.utcnow()


# ===================================
# PREMIUM NOTIFICATION SERVICE
# ===================================

class PremiumNotificationService:
    """
    Premium Notification Service with:
    - In-App Notifications
    - Email Digests
    - Slack/Discord Integration
    - Notification Preferences
    - Multiple Channels
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Load config from env
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
    
    # ===================================
    # IN-APP NOTIFICATIONS
    # ===================================
    
    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        type: str,
        priority: str = 'normal',
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create in-app notification"""
        
        # Convert string types to enums
        try:
            notification_type = NotificationType(type)
            notification_priority = NotificationPriority(priority)
        except ValueError:
            raise ValueError(f"Invalid notification type '{type}' or priority '{priority}'")
        
        # Create notification using the model function
        notification = create_notification(
            user_id=str(user_id),
            type=notification_type,
            title=title,
            message=message,
            priority=notification_priority,
            action_url=action_url,
            metadata=metadata
        )
        
        logger.info(f"Created notification for user {user_id}: {title}")
        
        return {
            'id': notification.id,
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': type,
            'priority': priority,
            'action_url': action_url,
            'metadata': metadata,
            'read': False,
            'created_at': notification.created_at.isoformat(),
        }
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's notifications"""
        
        # Create query parameters
        query = NotificationQuery(
            user_id=str(user_id),
            is_read=unread_only if unread_only else None,
            limit=limit
        )
        
        # Query notifications
        notifications = query_notifications(query)
        
        # Convert to response format
        result = []
        for notification in notifications:
            result.append({
                'id': notification.id,
                'user_id': int(notification.user_id),
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'priority': notification.priority,
                'action_url': notification.action_url,
                'read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'metadata': notification.metadata
            })
        
        return result
    
    async def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """Mark notification as read"""
        
        notification = mark_notification_read(notification_id, str(user_id))
        if notification:
            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            return True
        else:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return False
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read"""
        
        count = mark_all_notifications_read(str(user_id))
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count
    
    async def delete_notification(self, notification_id: str, user_id: int) -> bool:
        """Delete notification"""
        
        success = delete_notification(notification_id, str(user_id))
        if success:
            logger.info(f"Deleted notification {notification_id} for user {user_id}")
        else:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
        return success
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        
        return get_unread_count(str(user_id))
    
    # ===================================
    # EMAIL DIGESTS
    # ===================================
    
    async def send_daily_digest(self, user_id: int) -> Dict[str, Any]:
        """Send daily digest email"""
        
        if not self.email_enabled:
            return {'status': 'skipped', 'reason': 'email_disabled'}
        
        user = self.db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            return {'status': 'error', 'reason': 'user_not_found'}
        
        # Get summary data for last 24h
        summary = await self._get_daily_summary(user_id)
        
        # Send email via email_service
        try:
            await email_service.send_digest(
                recipient=user.email,
                digest_type='daily',
                summary=summary
            )
            logger.info(f"Sent daily digest to {user.email}")
            return {
                'status': 'sent',
                'to': user.email,
                'type': 'daily_digest',
                'summary': summary,
                'sent_at': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to send daily digest to {user.email}: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    async def send_weekly_digest(self, user_id: int) -> Dict[str, Any]:
        """Send weekly digest email"""
        
        if not self.email_enabled:
            return {'status': 'skipped', 'reason': 'email_disabled'}
        
        user = self.db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            return {'status': 'error', 'reason': 'user_not_found'}
        
        # Get summary data for last 7 days
        summary = await self._get_weekly_summary(user_id)
        
        # Send email via email_service (using generic notification)
        try:
            title = "Weekly Activity Digest"
            message = f"""
Weekly Summary:

Traces completed: {summary['traces_completed']}
Cases updated: {summary['cases_updated']}
Critical alerts: {summary['critical_alerts']}
High-risk addresses: {summary['high_risk_addresses']}

Top threat categories: {', '.join(summary['top_threat_categories'])}
            """.strip()
            
            await email_service.send_high_risk_alert(
                recipient=user.email,
                address="weekly-summary",
                risk_score=0.0,
                factors=[]
            )  # TODO: Create proper digest email method
            
            logger.info(f"Sent weekly digest to {user.email}")
            return {
                'status': 'sent',
                'to': user.email,
                'type': 'weekly_digest',
                'summary': summary,
                'sent_at': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to send weekly digest to {user.email}: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    async def _get_daily_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary data for last 24h"""
        # TODO: Replace with actual analytics queries
        # For now, return sample data that would come from analytics service
        return {
            'traces_completed': 15,
            'cases_updated': 3,
            'critical_alerts': 2,
            'high_risk_addresses': 5,
            'new_notifications': await self.get_unread_count(user_id),
        }
    
    async def _get_weekly_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary data for last 7 days"""
        # TODO: Replace with actual analytics queries
        return {
            'traces_completed': 87,
            'cases_updated': 12,
            'critical_alerts': 8,
            'high_risk_addresses': 23,
            'top_threat_categories': ['mixer', 'sanctions', 'scam'],
            'total_notifications': await self.get_unread_count(user_id),
        }
    
    # ===================================
    # SLACK INTEGRATION
    # ===================================
    
    async def send_slack_notification(
        self,
        message: str,
        title: Optional[str] = None,
        priority: str = 'normal',
        fields: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send notification to Slack"""
        
        if not self.slack_webhook_url:
            return {'status': 'skipped', 'reason': 'slack_not_configured'}
        
        # Build Slack message
        slack_message = {
            'text': title or message,
            'attachments': []
        }
        
        # Add color based on priority
        color_map = {
            'low': '#36a64f',  # green
            'normal': '#2196F3',  # blue
            'high': '#ff9800',  # orange
            'critical': '#f44336',  # red
        }
        
        attachment = {
            'color': color_map.get(priority, '#2196F3'),
            'text': message if title else None,
            'fields': fields or [],
            'ts': int(datetime.utcnow().timestamp())
        }
        
        if attachment['text'] or attachment['fields']:
            slack_message['attachments'].append(attachment)
        
        # Send to Slack
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                        return {'status': 'sent', 'channel': 'slack'}
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        return {'status': 'error', 'reason': f'status_{response.status}'}
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    # ===================================
    # DISCORD INTEGRATION
    # ===================================
    
    async def send_discord_notification(
        self,
        message: str,
        title: Optional[str] = None,
        priority: str = 'normal',
        fields: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Send notification to Discord"""
        
        if not self.discord_webhook_url:
            return {'status': 'skipped', 'reason': 'discord_not_configured'}
        
        # Build Discord embed
        color_map = {
            'low': 0x36a64f,  # green
            'normal': 0x2196F3,  # blue
            'high': 0xff9800,  # orange
            'critical': 0xf44336,  # red
        }
        
        embed = {
            'title': title,
            'description': message,
            'color': color_map.get(priority, 0x2196F3),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if fields:
            embed['fields'] = [
                {'name': f['title'], 'value': f['value'], 'inline': f.get('short', False)}
                for f in fields
            ]
        
        discord_message = {
            'embeds': [embed]
        }
        
        # Send to Discord
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook_url,
                    json=discord_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status in [200, 204]:
                        logger.info("Discord notification sent successfully")
                        return {'status': 'sent', 'channel': 'discord'}
                    else:
                        logger.error(f"Discord notification failed: {response.status}")
                        return {'status': 'error', 'reason': f'status_{response.status}'}
        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    # ===================================
    # NOTIFICATION PREFERENCES
    # ===================================
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's notification preferences"""
        
        settings = get_user_notification_settings(str(user_id))
        if settings:
            return {
                'user_id': user_id,
                'email_enabled': settings.email_enabled,
                'slack_enabled': settings.slack_enabled,
                'in_app_enabled': settings.in_app_enabled,
                'webhook_enabled': settings.webhook_enabled,
                'sms_enabled': settings.sms_enabled,
                'alert_notifications': settings.alert_notifications,
                'case_notifications': settings.case_notifications,
                'report_notifications': settings.report_notifications,
                'mention_notifications': settings.mention_notifications,
                'task_notifications': settings.task_notifications,
                'min_priority': settings.min_priority,
                'quiet_hours': {
                    'enabled': bool(settings.quiet_hours_start and settings.quiet_hours_end),
                    'start': settings.quiet_hours_start,
                    'end': settings.quiet_hours_end,
                    'timezone': 'UTC'
                },
                'notification_types': {
                    'alerts': {'email': settings.alert_notifications, 'in_app': True, 'slack': settings.slack_enabled},
                    'trace_complete': {'email': False, 'in_app': True, 'slack': False},
                    'case_update': {'email': settings.case_notifications, 'in_app': True, 'slack': False},
                    'payment': {'email': True, 'in_app': True, 'slack': False},
                    'system': {'email': False, 'in_app': True, 'slack': False},
                },
                'digests': {
                    'daily': False,  # TODO: Add to settings model
                    'weekly': True,
                }
            }
        else:
            # Return default preferences
            return {
                'user_id': user_id,
                'email_enabled': True,
                'slack_enabled': False,
                'in_app_enabled': True,
                'quiet_hours': {
                    'enabled': False,
                    'start': '22:00',
                    'end': '08:00',
                    'timezone': 'UTC'
                },
                'notification_types': {
                    'alerts': {'email': True, 'in_app': True, 'slack': False},
                    'trace_complete': {'email': False, 'in_app': True, 'slack': False},
                    'case_update': {'email': True, 'in_app': True, 'slack': False},
                    'payment': {'email': True, 'in_app': True, 'slack': False},
                    'system': {'email': False, 'in_app': True, 'slack': False},
                },
                'digests': {
                    'daily': False,
                    'weekly': True,
                }
            }
    
    async def update_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's notification preferences"""
        
        # Map the preferences to the settings model fields
        settings_kwargs = {}
        
        # Channel preferences
        settings_kwargs['email_enabled'] = preferences.get('email_enabled', True)
        settings_kwargs['slack_enabled'] = preferences.get('slack_enabled', False)
        settings_kwargs['in_app_enabled'] = preferences.get('in_app_enabled', True)
        settings_kwargs['webhook_enabled'] = preferences.get('webhook_enabled', False)
        settings_kwargs['sms_enabled'] = preferences.get('sms_enabled', False)
        
        # Type preferences
        settings_kwargs['alert_notifications'] = preferences.get('alert_notifications', True)
        settings_kwargs['case_notifications'] = preferences.get('case_notifications', True)
        settings_kwargs['report_notifications'] = preferences.get('report_notifications', True)
        settings_kwargs['mention_notifications'] = preferences.get('mention_notifications', True)
        settings_kwargs['task_notifications'] = preferences.get('task_notifications', True)
        
        # Priority filter
        settings_kwargs['min_priority'] = preferences.get('min_priority', 'normal')
        
        # Quiet hours
        quiet_hours = preferences.get('quiet_hours', {})
        if quiet_hours.get('enabled'):
            settings_kwargs['quiet_hours_start'] = quiet_hours.get('start')
            settings_kwargs['quiet_hours_end'] = quiet_hours.get('end')
        else:
            settings_kwargs['quiet_hours_start'] = None
            settings_kwargs['quiet_hours_end'] = None
        
        # Update settings
        settings = update_notification_settings(str(user_id), **settings_kwargs)
        
        logger.info(f"Updated notification preferences for user {user_id}")
        
        return {
            'user_id': user_id,
            **preferences,
            'updated_at': settings.updated_at.isoformat(),
        }
    
    # ===================================
    # HELPER METHODS
    # ===================================
    
    async def should_send_notification(
        self,
        user_id: int,
        notification_type: str,
        channel: str
    ) -> bool:
        """Check if notification should be sent based on preferences"""
        
        prefs = await self.get_user_preferences(user_id)
        
        # Check if channel is enabled
        if not prefs.get(f'{channel}_enabled', False):
            return False
        
        # Check quiet hours for non-in-app channels
        if channel != 'in_app' and prefs['quiet_hours']['enabled']:
            now = datetime.utcnow()
            current_time = now.strftime('%H:%M')
            start_time = prefs['quiet_hours']['start']
            end_time = prefs['quiet_hours']['end']
            
            if start_time and end_time:
                # Check if current time is within quiet hours
                if start_time <= end_time:
                    # Same day range (e.g., 22:00 to 08:00 next day)
                    is_quiet = start_time <= current_time <= end_time
                else:
                    # Overnight range (e.g., 22:00 to 08:00)
                    is_quiet = current_time >= start_time or current_time <= end_time
                
                if is_quiet:
                    return False
        
        # Check notification type preferences
        type_prefs = prefs['notification_types'].get(notification_type, {})
        if not type_prefs.get(channel, False):
            return False
        
        return True
    
    # ===================================
    # UNIFIED SEND METHOD
    # ===================================
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        type: str,
        priority: str = 'normal',
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Send notification to multiple channels based on user preferences
        
        Args:
            user_id: UserORM ID
            title: Notification title
            message: Notification message
            type: Notification type ('alert', 'trace_complete', etc.)
            priority: Priority level ('low', 'normal', 'high', 'critical')
            action_url: Optional action URL
            metadata: Optional metadata
            channels: Optional list of channels to use (default: all enabled)
        
        Returns:
            Dict with results per channel
        """
        
        results = {
            'in_app': [],
            'email': [],
            'slack': [],
            'discord': [],
        }
        
        # Determine which channels to use
        if not channels:
            prefs = await self.get_user_preferences(user_id)
            channels = [
                ch for ch in ['in_app', 'email', 'slack', 'discord']
                if await self.should_send_notification(user_id, type, ch)
            ]
        
        # Send to each channel
        for channel in channels:
            try:
                if channel == 'in_app':
                    result = await self.create_notification(
                        user_id, title, message, type, priority, action_url, metadata
                    )
                    results['in_app'].append(result)
                
                elif channel == 'email':
                    # TODO: Send email
                    pass
                
                elif channel == 'slack':
                    result = await self.send_slack_notification(
                        message, title, priority
                    )
                    results['slack'].append(result)
                
                elif channel == 'discord':
                    result = await self.send_discord_notification(
                        message, title, priority
                    )
                    results['discord'].append(result)
            
            except Exception as e:
                logger.error(f"Error sending notification to {channel}: {e}")
                results[channel].append({
                    'status': 'error',
                    'reason': str(e)
                })
        
        return results
