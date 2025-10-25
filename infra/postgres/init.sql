-- Initialize TimescaleDB Extension
CREATE EXTENSION IF NOT EXISTS timescaledb;
-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Transactions Table (Timeseries)
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL,
    tx_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42),
    value NUMERIC(78, 0),
    gas_used BIGINT,
    gas_price BIGINT,
    chain VARCHAR(32) NOT NULL,
    status INTEGER,
    risk_score NUMERIC(5, 4),
    cluster_id VARCHAR(66),
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('transactions', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions (tx_hash);
CREATE INDEX IF NOT EXISTS idx_from_address ON transactions (from_address);
CREATE INDEX IF NOT EXISTS idx_to_address ON transactions (to_address);
CREATE INDEX IF NOT EXISTS idx_block_number ON transactions (block_number);
CREATE INDEX IF NOT EXISTS idx_cluster_id ON transactions (cluster_id);

-- Risk Scores Table (Timeseries)
CREATE TABLE IF NOT EXISTS risk_scores (
    id BIGSERIAL,
    address VARCHAR(42) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    risk_score NUMERIC(5, 4) NOT NULL,
    risk_category VARCHAR(32),
    confidence NUMERIC(5, 4),
    features JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('risk_scores', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_risk_address ON risk_scores (address);

-- Labels Table
CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) NOT NULL,
    label VARCHAR(255) NOT NULL,
    category VARCHAR(64),
    source VARCHAR(128),
    confidence NUMERIC(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_label_address ON labels (address);
CREATE INDEX IF NOT EXISTS idx_label_category ON labels (category);

-- Trace Jobs Table
CREATE TABLE IF NOT EXISTS trace_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    start_address VARCHAR(42) NOT NULL,
    max_depth INTEGER DEFAULT 5,
    taint_model VARCHAR(32) DEFAULT 'proportional',
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    result JSONB,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_trace_status ON trace_jobs (status);
CREATE INDEX IF NOT EXISTS idx_trace_created ON trace_jobs (created_at DESC);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    address VARCHAR(42),
    tx_hash VARCHAR(66),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_alert_type ON alerts (alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alert_created ON alerts (created_at DESC);

-- Users Table (for RBAC)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'analyst',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(255),
    ip_address INET,
    details JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('audit_log', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log (action);

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_transaction_stats AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    chain,
    COUNT(*) as tx_count,
    AVG(risk_score) as avg_risk_score,
    SUM(value) as total_value
FROM transactions
GROUP BY day, chain
WITH NO DATA;

CREATE INDEX IF NOT EXISTS idx_daily_stats_day ON daily_transaction_stats (day DESC);

-- Refresh policy (refresh every hour)
CREATE OR REPLACE FUNCTION refresh_daily_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_transaction_stats;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- WP1: KYT/Monitoring Schemata
-- =============================

-- Monitoring Rules
CREATE TABLE IF NOT EXISTS monitor_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    scope VARCHAR(32) NOT NULL, -- address | tx | chain
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    expression JSONB NOT NULL,  -- JSON-DSL
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monitor_rules_enabled ON monitor_rules (enabled);
CREATE INDEX IF NOT EXISTS idx_monitor_rules_scope ON monitor_rules (scope);

-- Monitoring Alerts (separat zu bestehender "alerts"-Tabelle)
CREATE TABLE IF NOT EXISTS monitor_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID NOT NULL REFERENCES monitor_rules(id) ON DELETE CASCADE,
    entity_type VARCHAR(32) NOT NULL, -- address | tx | contract
    entity_id VARCHAR(128) NOT NULL,
    chain VARCHAR(32) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'open', -- open | assigned | snoozed | closed
    assignee UUID NULL REFERENCES users(id),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hits INTEGER NOT NULL DEFAULT 1,
    context JSONB,
    sla_due_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_monitor_alerts_rule ON monitor_alerts (rule_id);
CREATE INDEX IF NOT EXISTS idx_monitor_alerts_status ON monitor_alerts (status);
CREATE INDEX IF NOT EXISTS idx_monitor_alerts_severity ON monitor_alerts (severity);
CREATE INDEX IF NOT EXISTS idx_monitor_alerts_entity ON monitor_alerts (entity_type, entity_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_monitor_alert ON monitor_alerts (rule_id, entity_type, entity_id);

-- Alert Events (Audit Trail)
CREATE TABLE IF NOT EXISTS monitor_alert_events (
    id BIGSERIAL PRIMARY KEY,
    alert_id UUID NOT NULL REFERENCES monitor_alerts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor UUID NULL REFERENCES users(id),
    type VARCHAR(32) NOT NULL, -- created | status_changed | note_added
    payload JSONB
);

CREATE INDEX IF NOT EXISTS idx_monitor_alert_events_alert ON monitor_alert_events (alert_id);
CREATE INDEX IF NOT EXISTS idx_monitor_alert_events_type ON monitor_alert_events (type);

-- =============================
-- WP2: Case Management Schemata
-- =============================

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(256) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open', -- open | active | closed
    priority VARCHAR(16) NOT NULL DEFAULT 'medium', -- low | medium | high
    owner UUID NULL REFERENCES users(id),
    tags TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_status ON cases (status);
CREATE INDEX IF NOT EXISTS idx_cases_owner ON cases (owner);

CREATE TABLE IF NOT EXISTS case_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    item_type VARCHAR(16) NOT NULL, -- note | task | evidence | link
    content TEXT,
    content_json JSONB,
    actor UUID NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_items_case ON case_items (case_id);
CREATE INDEX IF NOT EXISTS idx_case_items_type ON case_items (item_type);

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    sha256 CHAR(64) NOT NULL,
    source_type VARCHAR(32) NOT NULL, -- trace | report | file
    uri TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    signature BYTEA NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_evidence_case_hash ON evidence (case_id, sha256);
