-- Migration: Add Demo User Fields for Two-Tier Demo System
-- Version: 007
-- Date: 2025-01-19

-- Add demo-related columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS demo_type VARCHAR(32);
ALTER TABLE users ADD COLUMN IF NOT EXISTS demo_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS demo_created_from_ip VARCHAR(64);

-- Add index for demo cleanup queries
CREATE INDEX IF NOT EXISTS idx_users_demo_expires ON users(demo_expires_at) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_demo_ip ON users(demo_created_from_ip) WHERE is_demo = TRUE;

-- Comment
COMMENT ON COLUMN users.is_demo IS 'Flag indicating if this is a demo user';
COMMENT ON COLUMN users.demo_type IS 'Type of demo: sandbox, live, or permanent';
COMMENT ON COLUMN users.demo_expires_at IS 'Timestamp when demo expires (NULL for permanent)';
COMMENT ON COLUMN users.demo_created_from_ip IS 'IP address that created this demo (abuse prevention)';
