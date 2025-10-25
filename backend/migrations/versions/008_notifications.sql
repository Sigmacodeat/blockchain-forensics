-- Migration: Notifications Table
-- Version: 008
-- Date: 2025-10-24

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(50) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notification content
    type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,

    -- Related entities
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(50),

    -- Delivery
    channels JSONB DEFAULT '["in_app"]'::jsonb,
    delivered_at JSONB DEFAULT '{}'::jsonb,

    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    action_url TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Indexes
    INDEX idx_notifications_user_id (user_id),
    INDEX idx_notifications_type (type),
    INDEX idx_notifications_priority (priority),
    INDEX idx_notifications_is_read (is_read),
    INDEX idx_notifications_created_at (created_at)
);

-- Create notification_settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    -- Channel preferences
    email_enabled BOOLEAN DEFAULT TRUE,
    slack_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    webhook_enabled BOOLEAN DEFAULT FALSE,
    sms_enabled BOOLEAN DEFAULT FALSE,

    -- Type preferences
    alert_notifications BOOLEAN DEFAULT TRUE,
    case_notifications BOOLEAN DEFAULT TRUE,
    report_notifications BOOLEAN DEFAULT TRUE,
    mention_notifications BOOLEAN DEFAULT TRUE,
    task_notifications BOOLEAN DEFAULT TRUE,

    -- Priority filters
    min_priority VARCHAR(20) DEFAULT 'normal',

    -- Quiet hours (24-hour format)
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,

    -- Template content
    subject_template VARCHAR(200) NOT NULL,
    body_template TEXT NOT NULL,

    -- Variables
    available_variables JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
