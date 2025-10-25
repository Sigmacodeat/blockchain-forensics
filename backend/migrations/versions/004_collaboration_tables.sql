-- Phase 2: Collaboration Tables
-- Case Collaborators and Comments for Team Features

-- Case Collaborators Table
CREATE TABLE IF NOT EXISTS case_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer', -- owner, editor, viewer
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    added_by UUID REFERENCES users(id),
    UNIQUE(case_id, user_id)
);

CREATE INDEX idx_case_collaborators_case ON case_collaborators(case_id);
CREATE INDEX idx_case_collaborators_user ON case_collaborators(user_id);
CREATE INDEX idx_case_collaborators_role ON case_collaborators(role);

-- Case Comments Table
CREATE TABLE IF NOT EXISTS case_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_case_comments_case ON case_comments(case_id);
CREATE INDEX idx_case_comments_user ON case_comments(user_id);
CREATE INDEX idx_case_comments_created ON case_comments(created_at DESC);

-- Optional: Cases table if not exists (minimal version)
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, closed
    addresses JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_cases_user ON cases(user_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created ON cases(created_at DESC);

COMMENT ON TABLE case_collaborators IS 'Team collaboration for investigation cases';
COMMENT ON TABLE case_comments IS 'Discussion threads for investigation cases';
COMMENT ON COLUMN case_collaborators.role IS 'Access level: owner (full), editor (modify), viewer (read-only)';
