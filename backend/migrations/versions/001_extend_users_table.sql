-- Migration: Extend users table with required fields
-- Date: 2025-10-19

-- Add missing columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(32) DEFAULT 'community' NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS features JSONB DEFAULT '[]'::jsonb NOT NULL;

-- Create unique index for username
CREATE UNIQUE INDEX IF NOT EXISTS users_username_key ON users(username) WHERE username IS NOT NULL;

-- Update existing users: set default username from email
UPDATE users SET username = split_part(email, '@', 1) WHERE username IS NULL;

-- Update existing users: set default plan based on role
UPDATE users SET plan = 'enterprise' WHERE role = 'admin' AND plan = 'community';

-- Update existing users: set updated_at to created_at
UPDATE users SET updated_at = created_at WHERE updated_at IS NULL;

-- Comment on columns
COMMENT ON COLUMN users.username IS 'Unique username for the user';
COMMENT ON COLUMN users.organization IS 'Organization name (optional)';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active';
COMMENT ON COLUMN users.updated_at IS 'Timestamp of last update';
COMMENT ON COLUMN users.plan IS 'Subscription plan: community, starter, pro, business, plus, enterprise';
COMMENT ON COLUMN users.features IS 'JSON array of enabled features';
