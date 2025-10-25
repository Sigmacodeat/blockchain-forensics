"""
Notification Management Models
For handling user notifications and alerts
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


class NotificationType(str, Enum):
    """Notification type enumeration"""
    ALERT = "alert"
    CASE_UPDATE = "case_update"
    REPORT_READY = "report_ready"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    USER_MENTION = "user_mention"
    TASK_ASSIGNMENT = "task_assignment"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class Notification(BaseModel):
    """Notification model"""
    id: str = Field(default_factory=lambda: f"notif_{datetime.utcnow().timestamp()}")
    user_id: str  # Target user ID

    # Notification content
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., max_length=200)
    message: str = Field(..., max_length=1000)

    # Related entities
    related_entity_type: Optional[str] = None  # e.g., "case", "alert", "report"
    related_entity_id: Optional[str] = None

    # Delivery
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    delivered_at: Optional[Dict[NotificationChannel, datetime]] = Field(default_factory=dict)

    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    action_url: Optional[str] = None  # URL to navigate to when clicked

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Auto-expire old notifications

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        notifications[self.id] = self


class NotificationSettings(BaseModel):
    """User notification preferences"""
    user_id: str

    # Channel preferences
    email_enabled: bool = True
    slack_enabled: bool = True
    in_app_enabled: bool = True
    webhook_enabled: bool = False
    sms_enabled: bool = False

    # Type preferences
    alert_notifications: bool = True
    case_notifications: bool = True
    report_notifications: bool = True
    mention_notifications: bool = True
    task_notifications: bool = True

    # Priority filters
    min_priority: NotificationPriority = NotificationPriority.NORMAL

    # Quiet hours (24-hour format)
    quiet_hours_start: Optional[str] = None  # e.g., "22:00"
    quiet_hours_end: Optional[str] = None    # e.g., "08:00"

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class NotificationTemplate(BaseModel):
    """Template for notification messages"""
    id: str = Field(default_factory=lambda: f"template_{datetime.utcnow().timestamp()}")
    name: str = Field(..., max_length=100)
    type: NotificationType
    channel: NotificationChannel

    # Template content
    subject_template: str = Field(..., max_length=200)
    body_template: str = Field(..., max_length=2000)

    # Variables that can be used in templates
    available_variables: List[str] = Field(default_factory=list)

    # Metadata
    is_system: bool = False  # System templates cannot be deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class NotificationQuery(BaseModel):
    """Query parameters for notifications"""
    user_id: Optional[str] = None
    type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    is_read: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


# In-Memory Storage (replace with PostgreSQL in production)
notifications: Dict[str, Notification] = {}
notification_settings: Dict[str, NotificationSettings] = {}
notification_templates: Dict[str, NotificationTemplate] = {}


def create_notification(
    user_id: str,
    type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[str] = None,
    channels: Optional[List[NotificationChannel]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    action_url: Optional[str] = None
) -> Notification:
    """Create a new notification"""
    notification = Notification(
        user_id=user_id,
        type=type,
        priority=priority,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        channels=channels or [NotificationChannel.IN_APP],
        metadata=metadata or {},
        action_url=action_url
    )

    notifications[notification.id] = notification
    return notification


def get_notification(notification_id: str) -> Optional[Notification]:
    """Get notification by ID"""
    return notifications.get(notification_id)


def mark_notification_read(notification_id: str, user_id: str) -> Optional[Notification]:
    """Mark notification as read"""
    notification = notifications.get(notification_id)
    if not notification or notification.user_id != user_id:
        return None

    notification.is_read = True
    notification.read_at = datetime.utcnow()

    return notification


def mark_all_notifications_read(user_id: str) -> int:
    """Mark all user's notifications as read"""
    count = 0
    for notification in notifications.values():
        if notification.user_id == user_id and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1

    return count


def delete_notification(notification_id: str, user_id: str) -> bool:
    """Delete a notification"""
    notification = notifications.get(notification_id)
    if not notification or notification.user_id != user_id:
        return False

    del notifications[notification_id]
    return True


def query_notifications(query: NotificationQuery) -> List[Notification]:
    """Query notifications with filters"""
    results = list(notifications.values())

    if query.user_id:
        results = [n for n in results if n.user_id == query.user_id]

    if query.type:
        results = [n for n in results if n.type == query.type]

    if query.priority:
        results = [n for n in results if n.priority == query.priority]

    if query.is_read is not None:
        results = [n for n in results if n.is_read == query.is_read]

    if query.start_date:
        results = [n for n in results if n.created_at >= query.start_date]

    if query.end_date:
        results = [n for n in results if n.created_at <= query.end_date]

    # Sort by creation date descending
    results.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    return results[query.offset : query.offset + query.limit]


def get_user_notification_settings(user_id: str) -> Optional[NotificationSettings]:
    """Get user's notification settings"""
    return notification_settings.get(user_id)


def update_notification_settings(
    user_id: str,
    **kwargs
) -> NotificationSettings:
    """Update user's notification settings"""
    settings = notification_settings.get(user_id)
    if not settings:
        settings = NotificationSettings(user_id=user_id)

    # Update provided fields
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    settings.updated_at = datetime.utcnow()
    notification_settings[user_id] = settings

    return settings


def create_notification_template(
    name: str,
    type: NotificationType,
    channel: NotificationChannel,
    subject_template: str,
    body_template: str,
    available_variables: Optional[List[str]] = None
) -> NotificationTemplate:
    """Create a notification template"""
    template = NotificationTemplate(
        name=name,
        type=type,
        channel=channel,
        subject_template=subject_template,
        body_template=body_template,
        available_variables=available_variables or []
    )

    notification_templates[template.id] = template
    return template


def get_notification_template(template_id: str) -> Optional[NotificationTemplate]:
    """Get template by ID"""
    return notification_templates.get(template_id)


def render_notification_template(
    template_id: str,
    variables: Dict[str, Any]
) -> Optional[tuple[str, str]]:
    """Render notification template with variables"""
    template = notification_templates.get(template_id)
    if not template:
        return None

    try:
        # Simple template rendering (in production, use Jinja2)
        subject = template.subject_template.format(**variables)
        body = template.body_template.format(**variables)
        return subject, body
    except (KeyError, ValueError):
        return None


def get_unread_count(user_id: str) -> int:
    """Get count of unread notifications for user"""
    return len([
        n for n in notifications.values()
        if n.user_id == user_id and not n.is_read
    ])
