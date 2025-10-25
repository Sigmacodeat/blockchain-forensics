-- Migration: Institutional Discount System
-- Version: 007
-- Date: 2025-10-19

-- Add organization and verification columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_type VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS institutional_discount_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS institutional_discount_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'none';
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_documents TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_notes TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_by UUID REFERENCES users(id);

-- Create institutional_verifications table
CREATE TABLE IF NOT EXISTS institutional_verifications (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_type VARCHAR(50) NOT NULL,
  organization_name VARCHAR(255),
  
  -- Documents
  document_type VARCHAR(50),
  document_url TEXT,
  document_filename VARCHAR(255),
  document_metadata JSONB,
  
  -- Status
  status VARCHAR(50) DEFAULT 'pending',
  reviewed_by UUID REFERENCES users(id),
  reviewed_at TIMESTAMP,
  
  -- Notes
  admin_notes TEXT,
  rejection_reason TEXT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_organization_type ON users(organization_type);
CREATE INDEX IF NOT EXISTS idx_users_verification_status ON users(verification_status);
CREATE INDEX IF NOT EXISTS idx_users_institutional_discount_verified ON users(institutional_discount_verified);
CREATE INDEX IF NOT EXISTS idx_institutional_verifications_user_id ON institutional_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_institutional_verifications_status ON institutional_verifications(status);

-- Comments
COMMENT ON COLUMN users.organization_type IS 'Type of organization: police, detective, lawyer, government, exchange, other';
COMMENT ON COLUMN users.verification_status IS 'Verification status: none, pending, approved, rejected';
COMMENT ON TABLE institutional_verifications IS 'Tracks institutional discount verification requests and documents';
