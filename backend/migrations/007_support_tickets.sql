-- Migration: Support Tickets System
-- Creates table for support tickets with country-based routing and AI auto-replies

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    country VARCHAR(2),  -- ISO 3166-1 alpha-2 (e.g., 'DE', 'US', 'JP')
    language VARCHAR(5) DEFAULT 'en',  -- e.g., 'de', 'en', 'ja'
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_agent TEXT,
    ip_address VARCHAR(45),  -- Supports IPv6
    referrer TEXT,
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    category VARCHAR(50) DEFAULT 'general' CHECK (category IN ('technical', 'billing', 'sales', 'general', 'feature_request')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    ai_reply TEXT,  -- AI-generated auto-reply sent to user
    admin_reply TEXT,  -- Human reply from support team
    metadata JSONB,  -- Additional context (e.g., source: "chatbot", urgency, etc.)
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Indexes for fast querying
CREATE INDEX idx_support_tickets_ticket_id ON support_tickets(ticket_id);
CREATE INDEX idx_support_tickets_email ON support_tickets(email);
CREATE INDEX idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_category ON support_tickets(category);
CREATE INDEX idx_support_tickets_country ON support_tickets(country);
CREATE INDEX idx_support_tickets_language ON support_tickets(language);
CREATE INDEX idx_support_tickets_created_at ON support_tickets(created_at DESC);

-- Full-text search on subject and message (für Admin-Suche)
CREATE INDEX idx_support_tickets_search ON support_tickets USING gin(to_tsvector('english', subject || ' ' || message));

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_support_ticket_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_support_ticket_timestamp
BEFORE UPDATE ON support_tickets
FOR EACH ROW
EXECUTE FUNCTION update_support_ticket_timestamp();

-- Comment
COMMENT ON TABLE support_tickets IS 'Support tickets from contact form and chatbot with multi-language and country-based routing';
COMMENT ON COLUMN support_tickets.country IS 'ISO 3166-1 alpha-2 country code for routing (e.g., DE, US, JP)';
COMMENT ON COLUMN support_tickets.language IS 'User preferred language for auto-replies (e.g., de, en, ja)';
COMMENT ON COLUMN support_tickets.ai_reply IS 'AI-generated auto-reply sent immediately to user';
COMMENT ON COLUMN support_tickets.admin_reply IS 'Human support team reply (optional)';
COMMENT ON COLUMN support_tickets.metadata IS 'Additional context: source (chatbot/web), urgency, etc.';
