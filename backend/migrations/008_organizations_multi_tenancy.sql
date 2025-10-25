-- Migration: Organizations & Multi-Tenancy
-- Adds complete SaaS multi-tenant isolation to the platform

-- ============================================
-- 1. CREATE ORGANIZATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    
    -- Owner & Contact
    owner_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    contact_email VARCHAR(255),
    
    -- Subscription
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'professional', 'enterprise')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'cancelled')),
    
    -- Billing
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    subscription_expires_at TIMESTAMP,
    
    -- Limits (based on plan)
    max_users INTEGER DEFAULT 1,
    max_cases INTEGER DEFAULT 10,
    max_traces_per_month INTEGER DEFAULT 100,
    
    -- Settings
    settings JSONB,
    features_enabled JSONB,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    trial_ends_at TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Indexes for organizations
CREATE INDEX idx_organizations_uuid ON organizations(uuid);
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_owner_id ON organizations(owner_id);
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_stripe_customer ON organizations(stripe_customer_id);


-- ============================================
-- 2. CREATE ORG_MEMBERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS org_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role & Permissions
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    permissions JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'invited', suspended')),
    invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP,
    joined_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(organization_id, user_id)
);

-- Indexes for org_members
CREATE INDEX idx_org_members_org_id ON org_members(organization_id);
CREATE INDEX idx_org_members_user_id ON org_members(user_id);
CREATE INDEX idx_org_members_role ON org_members(role);
CREATE INDEX idx_org_members_status ON org_members(status);


-- ============================================
-- 3. ADD organization_id TO EXISTING TABLES
-- ============================================

-- Cases
ALTER TABLE cases ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_cases_organization_id ON cases(organization_id);

-- Reports  
ALTER TABLE reports ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_reports_organization_id ON reports(organization_id);

-- Comments
ALTER TABLE comments ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_comments_organization_id ON comments(organization_id);

-- Notifications
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_notifications_organization_id ON notifications(organization_id);

-- Audit Logs
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);

-- Chat Sessions
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_chat_sessions_organization_id ON chat_sessions(organization_id);

-- Support Tickets
ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_support_tickets_organization_id ON support_tickets(organization_id);


-- ============================================
-- 4. AUTO-UPDATE TRIGGERS
-- ============================================

-- Auto-update updated_at for organizations
CREATE OR REPLACE FUNCTION update_organization_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_organization_timestamp
BEFORE UPDATE ON organizations
FOR EACH ROW
EXECUTE FUNCTION update_organization_timestamp();

-- Auto-update updated_at for org_members
CREATE TRIGGER trigger_update_org_member_timestamp
BEFORE UPDATE ON org_members
FOR EACH ROW
EXECUTE FUNCTION update_organization_timestamp();


-- ============================================
-- 5. DEFAULT DATA
-- ============================================

-- Create default "Personal" organization for existing users
-- (Run this manually after checking existing users)
-- INSERT INTO organizations (uuid, name, slug, owner_id, plan, max_users)
-- SELECT 
--     gen_random_uuid()::text,
--     'Personal Workspace - ' || users.email,
--     'personal-' || users.id,
--     users.id,
--     users.plan,
--     CASE users.plan 
--         WHEN 'community' THEN 1
--         WHEN 'pro' THEN 5
--         WHEN 'enterprise' THEN 50
--         ELSE 1
--     END
-- FROM users
-- WHERE NOT EXISTS (
--     SELECT 1 FROM organizations WHERE owner_id = users.id
-- );


-- ============================================
-- 6. SECURITY POLICIES (ROW LEVEL SECURITY)
-- ============================================

-- Enable RLS on organizations
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Users can only see organizations they belong to
CREATE POLICY org_member_access ON organizations
FOR SELECT
USING (
    id IN (
        SELECT organization_id FROM org_members WHERE user_id = current_setting('app.current_user_id')::INTEGER
    )
);

-- Enable RLS on cases (tenant isolation)
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

CREATE POLICY case_tenant_isolation ON cases
FOR ALL
USING (
    organization_id IN (
        SELECT organization_id FROM org_members WHERE user_id = current_setting('app.current_user_id')::INTEGER
    )
);


-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE organizations IS 'Multi-tenant organizations for SaaS isolation';
COMMENT ON TABLE org_members IS 'Organization membership with roles and permissions';
COMMENT ON COLUMN organizations.uuid IS 'External UUID for API usage';
COMMENT ON COLUMN organizations.slug IS 'URL-safe identifier (e.g., acme-corp)';
COMMENT ON COLUMN organizations.max_users IS 'Maximum users allowed based on plan';
COMMENT ON COLUMN organizations.max_cases IS 'Maximum cases allowed based on plan';
COMMENT ON COLUMN organizations.max_traces_per_month IS 'Monthly trace limit based on plan';
COMMENT ON COLUMN org_members.role IS 'Member role: owner, admin, member, viewer';
COMMENT ON COLUMN org_members.status IS 'Membership status: active, invited, suspended';
